"""
PunarVastra Backend API with AI Model Integration
Flask REST API for textile waste analysis and marketplace
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import base64
from datetime import datetime
import uuid
import io
from PIL import Image
import json

# AI/ML Libraries
try:
    import numpy as np
    import cv2
    import tensorflow as tf
    from sklearn.cluster import KMeans
    HAS_AI_LIBS = True
except ImportError:
    HAS_AI_LIBS = False
    print("Warning: AI libraries not installed. Using simulation mode.")

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend connection

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def analyze_image_ai(image_path):
    """
    AI-powered image analysis for textile properties
    Analyzes color, texture, pattern, and quality
    """
    if not HAS_AI_LIBS:
        # Simulation mode if AI libraries not available
        return simulate_ai_analysis()
    
    try:
        # Read image
        img = cv2.imread(image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Color Analysis using K-means clustering
        pixels = img_rgb.reshape(-1, 3)
        kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Get dominant colors
        colors = kmeans.cluster_centers_.astype(int)
        dominant_color = colors[0]
        
        # Color classification
        color_name = classify_color(dominant_color)
        
        # Advanced Texture Analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Edge detection for texture
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Calculate variance for smoothness
        variance = np.var(gray)
        
        # Calculate standard deviation for texture complexity
        std_dev = np.std(gray)
        
        # Improved texture classification
        if edge_density < 0.05 and variance < 1000:
            texture = "Smooth Silk"
        elif edge_density < 0.10 and variance < 2000:
            texture = "Smooth Cotton"
        elif edge_density < 0.15 and std_dev < 40:
            texture = "Cotton"
        elif edge_density < 0.20 and std_dev < 60:
            texture = "Textured Cotton"
        elif edge_density > 0.25 and std_dev > 50:
            texture = "Denim"
        elif variance > 3000:
            texture = "Polyester Mix"
        elif edge_density > 0.20:
            texture = "Canvas/Heavy Cotton"
        else:
            texture = "Cotton Blend"
        
        # Pattern Detection (improved)
        pattern = detect_pattern(img_rgb, edge_density, variance)
        
        # Quality Assessment (based on image clarity and resolution)
        quality_score = assess_quality(img)
        
        # Estimated weight (based on image analysis - simplified)
        estimated_weight = estimate_weight(img.shape, edge_density)
        
        return {
            "color": color_name,
            "color_hex": rgb_to_hex(dominant_color),
            "texture": texture,
            "pattern": pattern,
            "quality": quality_score,
            "quality_rating": get_quality_rating(quality_score),
            "estimated_weight": estimated_weight,
            "dominant_colors": [rgb_to_hex(c) for c in colors[:3]],
            "upcycling_ideas": get_upcycling_ideas(texture, pattern, color_name)
        }
    
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return simulate_ai_analysis()


def get_upcycling_ideas(texture, pattern, color):
    """Generate upcycling ideas based on material properties"""
    ideas = []
    
    # Texture-based ideas
    if "Cotton" in texture:
        ideas.extend([
            "Tote bags and shopping bags",
            "Quilts and patchwork blankets",
            "Cushion covers and pillow cases",
            "Kitchen towels and napkins",
            "Eco-friendly gift wrapping"
        ])
    elif "Denim" in texture:
        ideas.extend([
            "Denim jackets and vests",
            "Tote bags and backpacks",
            "Aprons and work wear",
            "Home organizers and wall pockets",
            "Pet accessories and toys"
        ])
    elif "Silk" in texture:
        ideas.extend([
            "Scarves and accessories",
            "Premium cushion covers",
            "Decorative wall hangings",
            "Gift wrapping and packaging",
            "Jewelry pouches"
        ])
    elif "Polyester" in texture:
        ideas.extend([
            "Outdoor cushions and covers",
            "Reusable shopping bags",
            "Sports and gym bags",
            "Waterproof pouches",
            "Pet beds and accessories"
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
    if "Patchwork" in pattern or "Floral" in pattern:
        ideas.append("Bohemian style clothing")
        ideas.append("Decorative wall art")
    
    # Return top 5 most relevant ideas
    return ideas[:5]


def simulate_ai_analysis():
    """Fallback simulation when AI libraries unavailable"""
    import random
    
    colors = [
        "Multi-color (Red, Blue, Beige)",
        "Pink/Coral Palette",
        "Denim Blue with Patches",
        "Earthy Tones",
        "Vibrant Mix"
    ]
    
    textures = [
        "Cotton Quilted",
        "Denim",
        "Silk Blend",
        "Cotton Canvas",
        "Polyester Mix"
    ]
    
    patterns = [
        "Patchwork",
        "Striped",
        "Floral",
        "Geometric",
        "Abstract"
    ]
    
    selected_color = random.choice(colors)
    selected_texture = random.choice(textures)
    selected_pattern = random.choice(patterns)
    
    return {
        "color": selected_color,
        "color_hex": "#d4af37",
        "texture": selected_texture,
        "pattern": selected_pattern,
        "quality": round(random.uniform(0.7, 0.95), 2),
        "quality_rating": "Excellent",
        "estimated_weight": round(random.uniform(1.0, 5.0), 1),
        "dominant_colors": ["#d4af37", "#c94b7d", "#667eea"],
        "upcycling_ideas": get_upcycling_ideas(selected_texture, selected_pattern, selected_color)
    }


def classify_color(rgb):
    """Classify RGB color into named category with better accuracy"""
    r, g, b = rgb
    
    # Calculate color properties
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val - min_val
    
    # Check for grayscale
    if diff < 30:
        if max_val > 200:
            return "White/Light"
        elif max_val < 80:
            return "Black/Dark"
        else:
            return "Gray"
    
    # Red family
    if r > g + 30 and r > b + 30:
        if r > 180 and g < 100:
            return "Red"
        elif r > 150 and g > 80 and g < 150:
            return "Pink/Coral"
        elif r > 140 and g > 60:
            return "Orange/Peach"
        else:
            return "Red/Pink"
    
    # Blue family
    elif b > r + 30 and b > g + 30:
        if b > 150 and r < 100:
            return "Blue"
        elif b > 100 and r > 80:
            return "Purple/Violet"
        else:
            return "Blue"
    
    # Green family
    elif g > r + 30 and g > b + 30:
        if g > 150 and b < 100:
            return "Green"
        elif g > 150 and b > 100:
            return "Teal/Cyan"
        else:
            return "Green"
    
    # Yellow family
    elif r > 150 and g > 150 and b < 120:
        if r > 200 and g > 200:
            return "Yellow"
        else:
            return "Yellow/Gold"
    
    # Brown family
    elif r > 100 and g > 60 and b < 100 and r > g and g > b:
        return "Brown/Tan"
    
    # Multi-color (when no dominant color)
    else:
        return "Multi-color"


def detect_pattern(img, edge_density, variance):
    """Detect pattern type from image with improved accuracy"""
    # High edge density suggests complex patterns
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


def assess_quality(img):
    """Assess quality based on image properties"""
    # Higher resolution = higher quality
    pixels = img.shape[0] * img.shape[1]
    
    # Calculate blur (Laplacian variance)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if HAS_AI_LIBS else None
    
    if gray is not None:
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_normalized = min(blur_score / 1000, 1.0)
    else:
        blur_normalized = 0.8
    
    # Resolution score
    resolution_score = min(pixels / 1000000, 1.0)
    
    # Combined quality score
    quality = (blur_normalized * 0.6 + resolution_score * 0.4)
    return round(quality, 2)


def get_quality_rating(score):
    """Convert quality score to rating"""
    if score >= 0.9:
        return "Premium"
    elif score >= 0.75:
        return "Excellent"
    elif score >= 0.6:
        return "Good"
    else:
        return "Fair"


def estimate_weight(shape, edge_density):
    """Estimate weight based on image properties"""
    # Simplified weight estimation
    base_weight = 1.5
    density_factor = 1 + edge_density
    return round(base_weight * density_factor, 1)


def rgb_to_hex(rgb):
    """Convert RGB to hex color"""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def home():
    """API root endpoint"""
    return jsonify({
        "message": "PunarVastra API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/upload",
            "materials": "/api/materials",
            "analyze": "/api/analyze",
            "orders": "/api/orders",
            "images": "/uploads/<filename>"
        },
        "ai_enabled": HAS_AI_LIBS
    })


@app.route('/uploads/<filename>')
def serve_image(filename):
    """Serve uploaded images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/upload', methods=['POST'])
def upload_material():
    """
    Upload textile material image for AI analysis
    Factory Dashboard endpoint
    """
    try:
        # Check if image is in request
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save file
            file.save(filepath)
            
            # Get additional form data from factory
            quantity = request.form.get('quantity', '')  # Factory must provide quantity
            price_per_kg = request.form.get('price_per_kg', '')  # Factory must provide price
            factory_id = request.form.get('factory_id', 'FAC-001')
            factory_name = request.form.get('factory_name', 'Factory')
            
            # Validate required fields
            if not quantity:
                return jsonify({"error": "Quantity is required"}), 400
            if not price_per_kg:
                return jsonify({"error": "Price per kg is required"}), 400
            
            # Perform AI analysis
            ai_analysis = analyze_image_ai(filepath)
            
            # Create material record
            material = {
                "id": f"MAT-{uuid.uuid4().hex[:8].upper()}",
                "factory_id": factory_id,
                "factory_name": factory_name,
                "image_path": filepath,
                "image_url": f"/uploads/{unique_filename}",
                "uploaded_at": datetime.now().isoformat(),
                "quantity": float(quantity),  # Quantity in kg
                "price_per_kg": float(price_per_kg),  # Price set by factory
                "total_amount": float(quantity) * float(price_per_kg),
                "status": "available",
                "ai_analysis": ai_analysis
            }
            
            # Store in database
            materials_db.append(material)
            save_materials()  # Persist to file
            
            return jsonify({
                "success": True,
                "message": "Material uploaded and analyzed successfully",
                "material": material
            }), 201
        
        return jsonify({"error": "Invalid file type"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_image():
    """
    Analyze image without saving
    Quick analysis endpoint
    """
    try:
        data = request.json
        
        if 'image' not in data:
            return jsonify({"error": "No image data provided"}), 400
        
        # Decode base64 image
        image_data = data['image'].split(',')[1] if ',' in data['image'] else data['image']
        image_bytes = base64.b64decode(image_data)
        
        # Save temporary file for analysis
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4()}.jpg")
        with open(temp_path, 'wb') as f:
            f.write(image_bytes)
        
        # Analyze
        analysis = analyze_image_ai(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify({
            "success": True,
            "analysis": analysis
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/materials', methods=['GET'])
def get_materials():
    """
    Get all available materials
    Artisan Marketplace endpoint
    """
    # Get query parameters for filtering
    color = request.args.get('color', 'all')
    texture = request.args.get('texture', 'all')
    
    # Filter materials
    filtered_materials = materials_db.copy()
    
    if color != 'all':
        filtered_materials = [
            m for m in filtered_materials 
            if color.lower() in m['ai_analysis']['color'].lower()
        ]
    
    if texture != 'all':
        filtered_materials = [
            m for m in filtered_materials 
            if texture.lower() in m['ai_analysis']['texture'].lower()
        ]
    
    return jsonify({
        "success": True,
        "count": len(filtered_materials),
        "materials": filtered_materials
    }), 200


@app.route('/api/materials/<material_id>', methods=['GET'])
def get_material(material_id):
    """Get specific material by ID"""
    material = next((m for m in materials_db if m['id'] == material_id), None)
    
    if material:
        return jsonify({
            "success": True,
            "material": material
        }), 200
    
    return jsonify({"error": "Material not found"}), 404


@app.route('/api/factory/materials', methods=['GET'])
def get_factory_materials():
    """
    Get materials uploaded by specific factory
    Factory Dashboard endpoint - shows factory's own uploads
    """
    factory_id = request.args.get('factory_id', 'FAC-001')
    
    # Filter materials by factory
    factory_materials = [m for m in materials_db if m['factory_id'] == factory_id]
    
    return jsonify({
        "success": True,
        "count": len(factory_materials),
        "materials": factory_materials
    }), 200


@app.route('/api/orders', methods=['POST'])
def create_order():
    """
    Create purchase order
    Artisan purchase endpoint
    """
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['material_id', 'artisan_name', 'email', 'quantity', 'address']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Check if material exists
        material = next((m for m in materials_db if m['id'] == data['material_id']), None)
        
        if not material:
            return jsonify({"error": "Material not found"}), 404
        
        if material['status'] != 'available':
            return jsonify({"error": "Material not available"}), 400
        
        # Check if requested quantity is available
        if float(data['quantity']) > material['quantity']:
            return jsonify({"error": f"Requested quantity ({data['quantity']} kg) exceeds available quantity ({material['quantity']} kg)"}), 400
        
        # Calculate total amount
        total_amount = float(data['quantity']) * material['price_per_kg']
        
        # Create order
        order = {
            "id": f"ORD-{uuid.uuid4().hex[:8].upper()}",
            "material_id": data['material_id'],
            "material_details": {
                "color": material['ai_analysis']['color'],
                "texture": material['ai_analysis']['texture'],
                "pattern": material['ai_analysis']['pattern']
            },
            "factory_id": material['factory_id'],
            "factory_name": material['factory_name'],
            "artisan_name": data['artisan_name'],
            "contact": data.get('contact', ''),
            "email": data['email'],
            "quantity": float(data['quantity']),
            "unit_price": material['price_per_kg'],
            "total_amount": total_amount,
            "address": data['address'],
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # Update material quantity (reduce available quantity)
        material['quantity'] -= float(data['quantity'])
        
        # If no quantity left, mark as sold
        if material['quantity'] <= 0:
            material['status'] = 'sold'
        
        # Store order
        orders_db.append(order)
        save_orders()  # Persist to file
        save_materials()  # Save updated material quantity
        
        return jsonify({
            "success": True,
            "message": "Order created successfully",
            "order": order
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get all orders"""
    return jsonify({
        "success": True,
        "count": len(orders_db),
        "orders": orders_db
    }), 200


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get platform statistics"""
    total_materials = len(materials_db)
    available_materials = len([m for m in materials_db if m['status'] == 'available'])
    total_orders = len(orders_db)
    total_revenue = sum(order['total_amount'] for order in orders_db)
    
    return jsonify({
        "success": True,
        "stats": {
            "total_materials": total_materials,
            "available_materials": available_materials,
            "sold_materials": total_materials - available_materials,
            "total_orders": total_orders,
            "total_revenue": total_revenue
        }
    }), 200


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_price(ai_analysis):
    """Calculate price per kg based on quality"""
    base_price = 300
    quality_multiplier = ai_analysis['quality']
    
    if 'premium' in ai_analysis['quality_rating'].lower():
        multiplier = 1.5
    elif 'excellent' in ai_analysis['quality_rating'].lower():
        multiplier = 1.3
    elif 'good' in ai_analysis['quality_rating'].lower():
        multiplier = 1.1
    else:
        multiplier = 1.0
    
    return round(base_price * multiplier * quality_multiplier)


def calculate_order_total(material, quantity):
    """Calculate order total amount"""
    try:
        quantity_kg = float(quantity)
        price_per_kg = material['price_per_kg']
        return round(quantity_kg * price_per_kg, 2)
    except:
        return 0


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 PunarVastra Backend API")
    print("=" * 60)
    print(f"AI Libraries: {'✅ Enabled' if HAS_AI_LIBS else '⚠️  Simulation Mode'}")
    print(f"Upload Folder: {UPLOAD_FOLDER}")
    print(f"Server: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
