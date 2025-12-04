from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import base64
from datetime import datetime
import uuid
import io
from PIL import Image, ImageStat
import json
from collections import Counter

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database files
DB_FILE = 'materials_db.json'
ORDERS_FILE = 'orders_db.json'

materials_db = []
orders_db = []


def load_database():
    """Load materials and orders from JSON files"""
    global materials_db, orders_db
    
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f:
                materials_db = json.load(f)
        print(f"Loaded {len(materials_db)} materials from database")
    except Exception as e:
        print(f"Error loading materials: {e}")
        materials_db = []
    
    try:
        if os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, 'r') as f:
                orders_db = json.load(f)
        print(f"Loaded {len(orders_db)} orders from database")
    except Exception as e:
        print(f"Error loading orders: {e}")
        orders_db = []


def save_materials():
    """Save materials to JSON file"""
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(materials_db, f, indent=2)
        print(f"Saved {len(materials_db)} materials to database")
    except Exception as e:
        print(f"Error saving materials: {e}")


def save_orders():
    """Save orders to JSON file"""
    try:
        with open(ORDERS_FILE, 'w') as f:
            json.dump(orders_db, f, indent=2)
        print(f"Saved {len(orders_db)} orders to database")
    except Exception as e:
        print(f"Error saving orders: {e}")


load_database()


def simple_color_detection(img):
    """Simple color detection from average RGB"""
    img_small = img.copy()
    img_small.thumbnail((100, 100))
    
    if img_small.mode != 'RGB':
        img_small = img_small.convert('RGB')
    
    pixels = list(img_small.getdata())
    
    # Calculate average color
    r_avg = sum(p[0] for p in pixels) / len(pixels)
    g_avg = sum(p[1] for p in pixels) / len(pixels)
    b_avg = sum(p[2] for p in pixels) / len(pixels)
    
    # Simple color classification
    if r_avg > 180 and g_avg < 100 and b_avg < 100:
        return "Red", "red"
    elif r_avg > 150 and g_avg > 100 and b_avg < 120:
        return "Orange/Pink", "orange"
    elif r_avg > 150 and g_avg > 150 and b_avg < 100:
        return "Yellow", "yellow"
    elif g_avg > 150 and r_avg < 120 and b_avg < 120:
        return "Green", "green"
    elif b_avg > 150 and r_avg < 120 and g_avg < 120:
        return "Blue", "blue"
    elif r_avg > 150 and b_avg > 150:
        return "Purple/Pink", "purple"
    elif r_avg > 200 and g_avg > 200 and b_avg > 200:
        return "White/Light", "white"
    elif r_avg < 80 and g_avg < 80 and b_avg < 80:
        return "Black/Dark", "black"
    else:
        return "Multi-color", "multi"


def simple_texture_detection(img):
    """Simple texture detection"""
    gray = img.convert('L')
    gray.thumbnail((150, 150))
    
    pixels = list(gray.getdata())
    
    # Calculate variance
    mean = sum(pixels) / len(pixels)
    variance = sum((p - mean) ** 2 for p in pixels) / len(pixels)
    
    # Simple texture classification
    if variance < 800:
        return "Smooth Silk", "silk"
    elif variance < 1500:
        return "Smooth Cotton", "cotton"
    elif variance < 2500:
        return "Cotton", "cotton"
    elif variance > 3000:
        return "Denim/Canvas", "denim"
    else:
        return "Cotton Blend", "cotton"


def analyze_image_simple(image_path):
    """Simple image analysis"""
    try:
        img = Image.open(image_path)
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Detect color
        color, color_cat = simple_color_detection(img)
        
        # Detect texture
        texture, texture_cat = simple_texture_detection(img)
        
        # Generate textile name
        textile_name = f"{color} {texture}"
        
        # Upcycling ideas
        if "cotton" in texture_cat:
            ideas = ["Tote bags", "Quilts", "Cushion covers", "Kitchen towels", "Gift wrapping"]
        elif "silk" in texture_cat:
            ideas = ["Scarves", "Premium cushions", "Wall hangings", "Jewelry pouches", "Gift wrap"]
        elif "denim" in texture_cat:
            ideas = ["Denim bags", "Aprons", "Jackets", "Organizers", "Pet accessories"]
        else:
            ideas = ["Shopping bags", "Home decor", "Craft projects", "Pouches", "Accessories"]
        
        result = {
            "textile_name": textile_name,
            "color": color,
            "color_category": color_cat,
            "texture": texture,
            "texture_category": texture_cat,
            "pattern": "Solid",
            "quality": 0.80,
            "quality_rating": "Good",
            "upcycling_ideas": ideas,
            "analysis_method": "Simple Analysis"
        }
        
        return result
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return {
            "textile_name": "Cotton Fabric",
            "color": "Multi-color",
            "color_category": "multi",
            "texture": "Cotton",
            "texture_category": "cotton",
            "pattern": "Solid",
            "quality": 0.75,
            "quality_rating": "Good",
            "upcycling_ideas": ["Bags", "Quilts", "Cushions", "Towels", "Wrapping"],
            "analysis_method": "Fallback"
        }


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return jsonify({
        "message": "PunarVastra API - Running",
        "version": "3.0",
        "status": "online",
        "materials_count": len(materials_db),
        "orders_count": len(orders_db)
    })


@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded images"""
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze image"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400
        
        # Save temporarily
        temp_filename = f"temp_{uuid.uuid4().hex}.jpg"
        temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
        file.save(temp_path)
        
        # Analyze
        analysis = analyze_image_simple(temp_path)
        
        # Cleanup
        try:
            os.remove(temp_path)
        except:
            pass
        
        return jsonify(analysis)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_material():
    """Upload material"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        file = request.files['image']
        
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file"}), 400
        
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
        
        # Analyze
        analysis = analyze_image_simple(filepath)
        
        # Create material
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
        
        materials_db.append(material)
        save_materials()
        
        return jsonify({
            "message": "Material uploaded successfully",
            "material": material
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/materials', methods=['GET'])
def get_materials():
    """Get all materials"""
    available = [m for m in materials_db if m.get('status') == 'available' and m.get('quantity', 0) > 0]
    return jsonify(available)


@app.route('/api/factory/materials', methods=['GET'])
def get_factory_materials():
    """Get factory materials"""
    factory_id = request.args.get('factory_id')
    if not factory_id:
        return jsonify({"error": "factory_id required"}), 400
    
    factory_mats = [m for m in materials_db if m.get('factory_id') == factory_id]
    return jsonify(factory_mats)


@app.route('/api/orders', methods=['GET', 'POST'])
def handle_orders():
    """Handle orders"""
    if request.method == 'GET':
        return jsonify(orders_db)
    
    try:
        data = request.json
        
        required = ['material_id', 'buyer_name', 'buyer_contact', 'buyer_email', 'quantity', 'delivery_address']
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing: {field}"}), 400
        
        material = next((m for m in materials_db if m['id'] == data['material_id']), None)
        if not material:
            return jsonify({"error": "Material not found"}), 404
        
        qty = float(data['quantity'])
        if qty > material['quantity']:
            return jsonify({"error": f"Only {material['quantity']} kg available"}), 400
        
        total = qty * material['price_per_kg']
        
        order = {
            "id": f"ORD-{uuid.uuid4().hex[:8].upper()}",
            "material_id": data['material_id'],
            "textile_name": material['ai_analysis']['textile_name'],
            "material_info": {
                "color": material['ai_analysis']['color'],
                "texture": material['ai_analysis']['texture']
            },
            "factory_name": material['factory_name'],
            "buyer_name": data['buyer_name'],
            "buyer_contact": data['buyer_contact'],
            "buyer_email": data['buyer_email'],
            "quantity": qty,
            "unit_price": material['price_per_kg'],
            "total_amount": round(total, 2),
            "delivery_address": data['delivery_address'],
            "status": "confirmed",
            "ordered_at": datetime.now().isoformat()
        }
        
        material['quantity'] = round(material['quantity'] - qty, 2)
        if material['quantity'] <= 0:
            material['status'] = 'sold'
        
        orders_db.append(order)
        save_orders()
        save_materials()
        
        return jsonify({
            "message": "Order placed successfully",
            "order": order
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
