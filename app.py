from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import base64
from datetime import datetime
import uuid
import io
from PIL import Image
import json
from collections import Counter

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database files
DB_FILE = 'materials_db.json'
ORDERS_FILE = 'orders_db.json'

# In-memory database (loaded from files)
materials_db = []
orders_db = []


def load_database():
    """Load materials and orders from JSON files"""
    global materials_db, orders_db
    
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f:
                materials_db = json.load(f)
    except Exception as e:
        print(f"Error loading materials database: {e}")
        materials_db = []
    
    try:
        if os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, 'r') as f:
                orders_db = json.load(f)
    except Exception as e:
        print(f"Error loading orders database: {e}")
        orders_db = []


def save_materials():
    """Save materials to JSON file"""
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(materials_db, f, indent=2)
    except Exception as e:
        print(f"Error saving materials database: {e}")


def save_orders():
    """Save orders to JSON file"""
    try:
        with open(ORDERS_FILE, 'w') as f:
            json.dump(orders_db, f, indent=2)
    except Exception as e:
        print(f"Error saving orders database: {e}")


# Load database on startup
load_database()


def get_dominant_colors(image, num_colors=5):
    """Extract dominant colors using PIL (no external ML libraries needed)"""
    # Resize image for faster processing
    img = image.copy()
    img.thumbnail((150, 150))
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Get all pixels
    pixels = list(img.getdata())
    
    # Count color frequencies
    color_counts = Counter(pixels)
    
    # Get most common colors
    most_common = color_counts.most_common(num_colors)
    
    return [color for color, count in most_common]


def classify_color_accurate(rgb):
    """Improved color classification with better accuracy"""
    r, g, b = rgb
    
    # Normalize to 0-1 range
    total = r + g + b
    if total == 0:
        return "Black"
    
    r_norm = r / total
    g_norm = g / total
    b_norm = b / total
    
    # Calculate brightness
    brightness = (r + g + b) / 3
    
    # Calculate saturation
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    if max_val == 0:
        saturation = 0
    else:
        saturation = (max_val - min_val) / max_val
    
    # Low saturation = grayscale
    if saturation < 0.15:
        if brightness > 200:
            return "White"
        elif brightness > 130:
            return "Light Gray"
        elif brightness > 60:
            return "Gray"
        else:
            return "Black/Dark"
    
    # Determine dominant hue
    if r > g and r > b:
        # Red dominant
        if r > 180 and g < 100 and b < 100:
            return "Red"
        elif r > 150 and g > 100 and b < 120:
            if g > 140:
                return "Orange"
            else:
                return "Pink/Coral"
        elif r > 130 and g > 50 and b < 80:
            return "Red/Pink"
        else:
            return "Reddish"
    
    elif g > r and g > b:
        # Green dominant
        if b > 120:
            return "Teal/Cyan"
        elif g > 150 and r < 100:
            return "Green"
        elif g > 100 and r > 80:
            return "Yellow/Green"
        else:
            return "Greenish"
    
    elif b > r and b > g:
        # Blue dominant
        if r > 100:
            return "Purple/Violet"
        elif b > 150:
            return "Blue"
        else:
            return "Blue/Navy"
    
    elif r > 150 and g > 150:
        # Yellow family
        if b < 100:
            return "Yellow/Gold"
        else:
            return "Beige/Cream"
    
    elif r > 100 and g > 60 and b < 80:
        # Brown family
        return "Brown/Tan"
    
    else:
        return "Multi-color"


def analyze_texture_pil(image):
    """Analyze texture using PIL image statistics"""
    # Convert to grayscale
    gray = image.convert('L')
    
    # Resize for processing
    gray.thumbnail((200, 200))
    
    # Get pixel values
    pixels = list(gray.getdata())
    
    # Calculate statistics
    mean_val = sum(pixels) / len(pixels)
    variance = sum((p - mean_val) ** 2 for p in pixels) / len(pixels)
    std_dev = variance ** 0.5
    
    # Count edge-like transitions
    width, height = gray.size
    edge_count = 0
    threshold = 30
    
    for y in range(height - 1):
        for x in range(width - 1):
            current = gray.getpixel((x, y))
            right = gray.getpixel((x + 1, y))
            down = gray.getpixel((x, y + 1))
            
            if abs(current - right) > threshold or abs(current - down) > threshold:
                edge_count += 1
    
    edge_density = edge_count / (width * height)
    
    # Classify texture based on statistics
    if variance < 500 and edge_density < 0.05:
        return "Smooth Silk", edge_density, variance
    elif variance < 1000 and edge_density < 0.10:
        return "Smooth Cotton", edge_density, variance
    elif variance < 2000 and edge_density < 0.15:
        return "Cotton", edge_density, variance
    elif variance < 3000 and edge_density < 0.20:
        return "Textured Cotton", edge_density, variance
    elif edge_density > 0.25 and std_dev > 40:
        return "Denim", edge_density, variance
    elif variance > 3500:
        return "Polyester Mix", edge_density, variance
    elif edge_density > 0.20:
        return "Canvas/Heavy Cotton", edge_density, variance
    else:
        return "Cotton Blend", edge_density, variance


def detect_pattern_improved(edge_density, variance):
    """Improved pattern detection"""
    if edge_density > 0.30:
        return "Complex Patchwork"
    elif edge_density > 0.22:
        return "Patchwork"
    elif edge_density > 0.15 and variance > 2500:
        return "Geometric"
    elif variance > 3500:
        return "Abstract/Mixed"
    elif edge_density < 0.08:
        return "Solid/Plain"
    elif 0.12 < edge_density < 0.18:
        return "Striped/Linear"
    else:
        return "Textured"


def assess_quality_pil(image, variance):
    """Assess quality based on image properties"""
    width, height = image.size
    pixels = width * height
    
    # Higher resolution = higher quality (up to a point)
    if pixels > 1000000:
        resolution_score = 0.4
    elif pixels > 500000:
        resolution_score = 0.35
    elif pixels > 100000:
        resolution_score = 0.3
    else:
        resolution_score = 0.2
    
    # Moderate variance suggests good detail
    if 1000 < variance < 4000:
        detail_score = 0.35
    elif 500 < variance < 5000:
        detail_score = 0.25
    else:
        detail_score = 0.15
    
    # Base quality
    base_score = 0.25
    
    total_score = base_score + resolution_score + detail_score
    
    return min(total_score, 0.98)


def get_quality_rating(score):
    """Convert quality score to rating"""
    if score >= 0.85:
        return "Excellent"
    elif score >= 0.70:
        return "Good"
    elif score >= 0.50:
        return "Fair"
    else:
        return "Basic"


def get_upcycling_ideas(texture, pattern, color):
    """Generate upcycling ideas based on material properties"""
    ideas = []
    
    # Texture-based ideas
    texture_lower = texture.lower()
    
    if "cotton" in texture_lower:
        ideas.extend([
            "Tote bags and shopping bags",
            "Quilts and patchwork blankets",
            "Cushion covers and pillow cases",
            "Kitchen towels and napkins",
            "Eco-friendly gift wrapping"
        ])
    elif "denim" in texture_lower:
        ideas.extend([
            "Denim jackets and vests",
            "Tote bags and backpacks",
            "Aprons and work wear",
            "Home organizers and wall pockets",
            "Pet accessories and toys"
        ])
    elif "silk" in texture_lower:
        ideas.extend([
            "Scarves and accessories",
            "Premium cushion covers",
            "Decorative wall hangings",
            "Gift wrapping and packaging",
            "Jewelry pouches"
        ])
    elif "polyester" in texture_lower:
        ideas.extend([
            "Outdoor cushions and covers",
            "Reusable shopping bags",
            "Sports and gym bags",
            "Waterproof pouches",
            "Pet beds and accessories"
        ])
    elif "canvas" in texture_lower:
        ideas.extend([
            "Heavy-duty tote bags",
            "Art canvas and paintings",
            "Outdoor furniture covers",
            "Tool organizers",
            "Durable aprons"
        ])
    else:
        ideas.extend([
            "Mixed fabric quilts",
            "Patchwork home decor",
            "Craft projects",
            "Fabric scrap art",
            "Multi-purpose bags"
        ])
    
    # Pattern-based additions
    if "Patchwork" in pattern or "Floral" in pattern or "Geometric" in pattern:
        ideas.append("Bohemian style clothing")
        ideas.append("Decorative wall art")
    
    # Return top 5 most relevant ideas
    return ideas[:5]


def analyze_image_improved(image_path):
    """
    Improved AI-powered image analysis using only PIL
    More accurate color and texture detection
    """
    try:
        # Open image with PIL
        img = Image.open(image_path)
        
        # Get dominant colors
        dominant_colors = get_dominant_colors(img, num_colors=3)
        main_color = dominant_colors[0]
        
        # Classify color accurately
        color_name = classify_color_accurate(main_color)
        
        # Analyze texture
        texture, edge_density, variance = analyze_texture_pil(img)
        
        # Detect pattern
        pattern = detect_pattern_improved(edge_density, variance)
        
        # Assess quality
        quality_score = assess_quality_pil(img, variance)
        quality_rating = get_quality_rating(quality_score)
        
        # Get upcycling ideas
        upcycling_ideas = get_upcycling_ideas(texture, pattern, color_name)
        
        # Convert RGB to hex
        color_hex = '#{:02x}{:02x}{:02x}'.format(main_color[0], main_color[1], main_color[2])
        
        return {
            "color": color_name,
            "color_hex": color_hex,
            "texture": texture,
            "pattern": pattern,
            "quality": round(quality_score, 2),
            "quality_rating": quality_rating,
            "estimated_weight": round(2.5 + (variance / 1000), 1),
            "dominant_colors": ['#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2]) for c in dominant_colors],
            "upcycling_ideas": upcycling_ideas,
            "analysis_method": "PIL-based (Accurate)"
        }
    
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        # Fallback with basic analysis
        return {
            "color": "Multi-color",
            "color_hex": "#d4af37",
            "texture": "Cotton Blend",
            "pattern": "Textured",
            "quality": 0.75,
            "quality_rating": "Good",
            "estimated_weight": 3.0,
            "dominant_colors": ["#d4af37", "#c94b7d", "#667eea"],
            "upcycling_ideas": get_upcycling_ideas("Cotton", "Textured", "Multi-color"),
            "analysis_method": "Fallback"
        }


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Routes
@app.route('/')
def home():
    return jsonify({
        "message": "PunarVastra API",
        "version": "3.0 - Improved AI",
        "status": "running",
        "endpoints": {
            "upload": "/api/upload",
            "analyze": "/api/analyze", 
            "materials": "/api/materials",
            "factory_materials": "/api/factory/materials?factory_id=FAC-001",
            "orders": "/api/orders",
            "images": "/uploads/<filename>"
        }
    })


@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded images"""
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze an uploaded image"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if file and allowed_file(file.filename):
            # Save temporarily
            temp_filename = f"temp_{uuid.uuid4().hex}.jpg"
            temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
            file.save(temp_path)
            
            # Analyze image
            analysis = analyze_image_improved(temp_path)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return jsonify(analysis)
        
        return jsonify({"error": "Invalid file type"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_material():
    """Upload material with image and details"""
    try:
        # Check for image
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400
        
        # Get form data
        quantity = float(request.form.get('quantity', 0))
        price_per_kg = float(request.form.get('price_per_kg', 0))
        factory_name = request.form.get('factory_name', 'Unknown Factory')
        factory_id = request.form.get('factory_id', 'FAC-001')
        
        if quantity <= 0 or price_per_kg <= 0:
            return jsonify({"error": "Invalid quantity or price"}), 400
        
        # Save image
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Analyze image
        analysis = analyze_image_improved(filepath)
        
        # Create material record
        material = {
            "id": f"MAT-{uuid.uuid4().hex[:8].upper()}",
            "factory_id": factory_id,
            "factory_name": factory_name,
            "image_url": f"/uploads/{filename}",
            "quantity": quantity,
            "price_per_kg": price_per_kg,
            "total_amount": round(quantity * price_per_kg, 2),
            "ai_analysis": analysis,
            "uploaded_at": datetime.now().isoformat(),
            "status": "available"
        }
        
        # Store in database
        materials_db.append(material)
        save_materials()  # Persist to file
        
        return jsonify({
            "message": "Material uploaded successfully",
            "material": material
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/materials', methods=['GET'])
def get_materials():
    """Get all materials from all factories"""
    # Filter only available materials
    available_materials = [m for m in materials_db if m.get('status') == 'available' and m.get('quantity', 0) > 0]
    return jsonify(available_materials)


@app.route('/api/factory/materials', methods=['GET'])
def get_factory_materials():
    """Get materials for a specific factory"""
    factory_id = request.args.get('factory_id')
    
    if not factory_id:
        return jsonify({"error": "factory_id required"}), 400
    
    factory_materials = [m for m in materials_db if m.get('factory_id') == factory_id]
    return jsonify(factory_materials)


@app.route('/api/orders', methods=['GET', 'POST'])
def handle_orders():
    """Handle order operations"""
    if request.method == 'GET':
        return jsonify(orders_db)
    
    elif request.method == 'POST':
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['material_id', 'artisan_name', 'contact', 'email', 'quantity', 'address']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            # Find material
            material = next((m for m in materials_db if m['id'] == data['material_id']), None)
            
            if not material:
                return jsonify({"error": "Material not found"}), 404
            
            # Check quantity
            requested_qty = float(data['quantity'])
            if requested_qty > material['quantity']:
                return jsonify({"error": f"Insufficient quantity. Available: {material['quantity']} kg"}), 400
            
            # Calculate total
            total_amount = requested_qty * material['price_per_kg']
            
            # Create order
            order = {
                "id": f"ORD-{uuid.uuid4().hex[:8].upper()}",
                "material_id": data['material_id'],
                "material_details": {
                    "color": material['ai_analysis']['color'],
                    "texture": material['ai_analysis']['texture'],
                    "pattern": material['ai_analysis']['pattern']
                },
                "factory_name": material['factory_name'],
                "artisan_name": data['artisan_name'],
                "contact": data['contact'],
                "email": data['email'],
                "quantity": requested_qty,
                "unit_price": material['price_per_kg'],
                "total_amount": round(total_amount, 2),
                "address": data['address'],
                "status": "pending",
                "ordered_at": datetime.now().isoformat()
            }
            
            # Update material quantity
            material['quantity'] = round(material['quantity'] - requested_qty, 2)
            if material['quantity'] <= 0:
                material['status'] = 'sold'
            
            # Store order
            orders_db.append(order)
            save_orders()  # Persist to file
            save_materials()  # Save updated material quantity
            
            return jsonify({
                "message": "Order created successfully",
                "order": order
            }), 201
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
