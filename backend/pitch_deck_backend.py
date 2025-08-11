#!/usr/bin/env python3
"""
AI Sales Pitch Generator - Clean Rewrite
Simple, working 2-3 page pitch generator with file upload
"""

import os
import json
import logging
import io
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv

# OpenAI
try:
    from openai import OpenAI
except ImportError:
    print("OpenAI not installed")
    OpenAI = None

# File processing
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None

# Load environment
load_dotenv()

# Flask app
app = Flask(__name__)
CORS(app, origins=["*"])

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
PORT = int(os.getenv('PORT', 5001))

# Initialize OpenAI
ai_client = None
if OPENAI_API_KEY and OpenAI:
    ai_client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info(f"OpenAI initialized with model: {OPENAI_MODEL}")
else:
    logger.warning("No OpenAI API key configured")

# Main HTML page
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Sales Pitch Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .content {
            display: grid;
            grid-template-columns: 500px 1fr;
            gap: 40px;
            padding: 40px;
        }
        
        .input-section {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        
        input, textarea, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            font-family: inherit;
        }
        
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        .file-upload-box {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: white;
            margin-bottom: 20px;
        }
        
        .file-upload-box:hover {
            background: #f0f4ff;
        }
        
        .file-upload-box.drag-over {
            background: #e8ecff;
            border-color: #4c63d2;
        }
        
        .file-icon {
            font-size: 3rem;
            margin-bottom: 10px;
        }
        
        .file-list {
            margin: 20px 0;
        }
        
        .file-item {
            background: white;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .remove-btn {
            background: #ff4444;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.3s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .output-section {
            background: white;
        }
        
        .output-content {
            padding: 30px;
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            min-height: 500px;
            max-height: 700px;
            overflow-y: auto;
        }
        
        .output-content h2 {
            color: #667eea;
            margin: 30px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        
        .output-content p {
            line-height: 1.8;
            margin-bottom: 15px;
            color: #444;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .placeholder {
            text-align: center;
            padding: 100px 20px;
            color: #999;
        }
        
        @media (max-width: 1024px) {
            .content {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AI Sales Pitch Generator</h1>
            <p>Create professional 2-3 page investor pitches</p>
        </div>
        
        <div class="content">
            <div class="input-section">
                <h2 style="margin-bottom: 25px;">Your Information</h2>
                
                <!-- File Upload -->
                <div id="dropZone" class="file-upload-box">
                    <div class="file-icon">📁</div>
                    <div>Drag files here or click to browse</div>
                    <small>PDF, Word, or text files</small>
                </div>
                <input type="file" id="fileInput" multiple accept=".pdf,.txt,.doc,.docx" style="display: none;">
                
                <div id="fileList" class="file-list"></div>
                
                <!-- Form -->
                <div class="form-group">
                    <label>Company Name *</label>
                    <input type="text" id="companyName" placeholder="TechVentures Inc.">
                </div>
                
                <div class="form-group">
                    <label>Industry *</label>
                    <input type="text" id="industry" placeholder="B2B SaaS, Fintech, etc.">
                </div>
                
                <div class="form-group">
                    <label>Problem You Solve *</label>
                    <textarea id="problem" placeholder="What problem does your company solve?"></textarea>
                </div>
                
                <div class="form-group">
                    <label>Your Solution *</label>
                    <textarea id="solution" placeholder="How do you solve this problem?"></textarea>
                </div>
                
                <div class="form-group">
                    <label>Funding Stage</label>
                    <select id="fundingStage">
                        <option value="seed">Seed</option>
                        <option value="series-a">Series A</option>
                        <option value="series-b">Series B</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Traction (Optional)</label>
                    <input type="text" id="traction" placeholder="100 customers, $1M ARR, etc.">
                </div>
                
                <button id="generateBtn" class="btn" onclick="generatePitch()">
                    Generate Sales Pitch
                </button>
            </div>
            
            <div class="output-section">
                <h2 style="margin-bottom: 20px;">Generated Pitch</h2>
                <div class="output-content" id="output">
                    <div class="placeholder">
                        <h3>Your pitch will appear here</h3>
                        <p>Fill in the form and click Generate</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Global variables
        let uploadedFiles = [];
        
        // Get elements
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileList = document.getElementById('fileList');
        
        // Click to upload
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });
        
        // Drag and drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('drag-over');
        });
        
        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            handleFiles(files);
        });
        
        // Prevent default drag behavior on document
        document.addEventListener('dragover', (e) => {
            e.preventDefault();
        });
        
        document.addEventListener('drop', (e) => {
            e.preventDefault();
        });
        
        // Handle files
        function handleFiles(files) {
            for (let file of files) {
                uploadedFiles.push(file);
            }
            updateFileList();
        }
        
        // Update file list display
        function updateFileList() {
            if (uploadedFiles.length === 0) {
                fileList.innerHTML = '';
                return;
            }
            
            fileList.innerHTML = uploadedFiles.map((file, idx) => `
                <div class="file-item">
                    <span>📄 ${file.name}</span>
                    <button class="remove-btn" onclick="removeFile(${idx})">Remove</button>
                </div>
            `).join('');
        }
        
        // Remove file
        function removeFile(index) {
            uploadedFiles.splice(index, 1);
            updateFileList();
        }
        
        // Generate pitch
        async function generatePitch() {
            const companyName = document.getElementById('companyName').value;
            const industry = document.getElementById('industry').value;
            const problem = document.getElementById('problem').value;
            const solution = document.getElementById('solution').value;
            const fundingStage = document.getElementById('fundingStage').value;
            const traction = document.getElementById('traction').value;
            
            if (!companyName || !industry || !problem || !solution) {
                alert('Please fill in all required fields');
                return;
            }
            
            const btn = document.getElementById('generateBtn');
            const output = document.getElementById('output');
            
            btn.disabled = true;
            btn.textContent = 'Generating...';
            
            output.innerHTML = '<div class="loading"><div class="spinner"></div><p>Creating your pitch...</p></div>';
            
            // Prepare form data
            const formData = new FormData();
            formData.append('company_name', companyName);
            formData.append('industry', industry);
            formData.append('problem', problem);
            formData.append('solution', solution);
            formData.append('funding_stage', fundingStage);
            formData.append('traction', traction);
            
            // Add files if any
            uploadedFiles.forEach(file => {
                formData.append('files', file);
            });
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.error) {
                    output.innerHTML = '<p style="color: red;">Error: ' + data.error + '</p>';
                } else {
                    displayPitch(data);
                }
            } catch (error) {
                output.innerHTML = '<p style="color: red;">Error generating pitch</p>';
            }
            
            btn.disabled = false;
            btn.textContent = 'Generate Sales Pitch';
        }
        
        // Display pitch
        function displayPitch(data) {
            const output = document.getElementById('output');
            
            let html = '<h1>' + (data.company_name || 'Sales Pitch') + '</h1>';
            
            if (data.executive_summary) {
                html += '<h2>Executive Summary</h2>';
                html += '<p>' + data.executive_summary + '</p>';
            }
            
            if (data.opportunity) {
                html += '<h2>The Opportunity</h2>';
                html += '<p>' + data.opportunity + '</p>';
            }
            
            if (data.why_us) {
                html += '<h2>Why ' + (data.company_name || 'Us') + '</h2>';
                html += '<p>' + data.why_us + '</p>';
            }
            
            output.innerHTML = html;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main page"""
    return Response(HTML_PAGE, mimetype='text/html')

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_available": ai_client is not None
    })

@app.route('/api/generate', methods=['POST'])
def generate_pitch():
    """Generate sales pitch with optional file context"""
    try:
        # Get form data
        company_name = request.form.get('company_name')
        industry = request.form.get('industry')
        problem = request.form.get('problem')
        solution = request.form.get('solution')
        funding_stage = request.form.get('funding_stage', 'seed')
        traction = request.form.get('traction', '')
        
        # Validate
        if not all([company_name, industry, problem, solution]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Process uploaded files if any
        additional_context = ""
        if 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                if file and file.filename:
                    content = extract_file_content(file)
                    if content:
                        additional_context += f"\n{content}\n"
        
        # Generate pitch
        pitch = generate_pitch_content(
            company_name,
            industry,
            problem,
            solution,
            funding_stage,
            traction,
            additional_context
        )
        
        return jsonify(pitch)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

def extract_file_content(file):
    """Extract text from uploaded file"""
    try:
        filename = file.filename.lower()
        file_content = file.read()
        
        if filename.endswith('.pdf') and PyPDF2:
            pdf = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            return text[:2000]  # Limit length
            
        elif filename.endswith('.txt'):
            return file_content.decode('utf-8', errors='ignore')[:2000]
            
        elif filename.endswith(('.doc', '.docx')) and Document:
            doc = Document(io.BytesIO(file_content))
            text = "\n".join([p.text for p in doc.paragraphs])
            return text[:2000]
            
    except Exception as e:
        logger.error(f"File extraction error: {e}")
    
    return ""

def generate_pitch_content(company_name, industry, problem, solution, funding_stage, traction, context=""):
    """Generate pitch using AI or template"""
    
    if ai_client:
        try:
            prompt = f"""
            Create a compelling 2-3 page sales pitch for investors.
            
            Company: {company_name}
            Industry: {industry}
            Problem: {problem}
            Solution: {solution}
            Stage: {funding_stage}
            Traction: {traction}
            
            Additional context from documents:
            {context[:1000]}
            
            Create exactly 3 sections:
            1. Executive Summary (200 words) - Overview and key metrics
            2. The Opportunity (300 words) - Problem, solution, market size
            3. Why {company_name} (200 words) - Team, traction, ask
            
            Write in professional, confident tone. Be specific.
            Return as JSON with keys: executive_summary, opportunity, why_us, company_name
            """
            
            response = ai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a pitch deck expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result['company_name'] = company_name
            return result
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
    
    # Fallback template
    return {
        "company_name": company_name,
        "executive_summary": f"{company_name} is revolutionizing {industry} by solving {problem}. {solution} We've achieved {traction or 'early traction'} and are raising {funding_stage} funding to accelerate growth.",
        "opportunity": f"The {industry} market is ripe for disruption. {problem} Our solution: {solution} With a growing market and clear customer demand, we're positioned to capture significant market share.",
        "why_us": f"Our team has deep {industry} expertise. {traction or 'We are building momentum'}. We're raising {funding_stage} funding to scale our solution and dominate the market."
    }

if __name__ == '__main__':
    print(f"""
    ========================================
    AI Sales Pitch Generator
    ========================================
    Starting on port {PORT}
    AI Status: {'Connected' if ai_client else 'Not configured'}
    
    Visit: http://localhost:{PORT}
    ========================================
    """)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)