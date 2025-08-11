#!/usr/bin/env python3
"""
AI Sales Pitch Generator
Clean implementation that actually uses uploaded files
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
    print("ERROR: OpenAI not installed. Run: pip install openai")
    exit(1)

# PDF processing
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
    print("Warning: PyPDF2 not installed. PDF support disabled.")

# Load environment
load_dotenv()

# Flask app
app = Flask(__name__)
CORS(app, origins=["*"])

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
PORT = int(os.getenv('PORT', 5001))

# Validate and initialize OpenAI
if not OPENAI_API_KEY:
    logger.error("FATAL: No OPENAI_API_KEY found in environment variables!")
    print("\n❌ ERROR: You must set OPENAI_API_KEY in your .env file")
    print("Example: OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx\n")
    exit(1)

try:
    ai_client = OpenAI(api_key=OPENAI_API_KEY)
    # Test the connection
    test = ai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=5
    )
    logger.info(f"✅ OpenAI connected successfully. Using model: {OPENAI_MODEL}")
except Exception as e:
    logger.error(f"❌ OpenAI connection failed: {e}")
    print(f"\n❌ ERROR: OpenAI API key is invalid or not working: {e}\n")
    exit(1)

# HTML Interface
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Sales Pitch Generator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%);
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
            grid-template-columns: 450px 1fr;
            gap: 40px;
            padding: 40px;
        }
        
        .input-panel {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            height: fit-content;
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
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        .upload-zone {
            border: 3px dashed #667eea;
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: white;
            margin-bottom: 20px;
        }
        
        .upload-zone:hover {
            background: #f8f9ff;
            border-color: #4c63d2;
        }
        
        .upload-zone.dragging {
            background: #e8ecff;
            border-color: #4c63d2;
            transform: scale(1.02);
        }
        
        .file-list {
            margin: 20px 0;
        }
        
        .file-item {
            background: white;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid #e0e0e0;
        }
        
        .file-name {
            flex: 1;
            font-weight: 500;
        }
        
        .remove-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        .remove-btn:hover {
            background: #c82333;
        }
        
        .generate-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s;
        }
        
        .generate-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .generate-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .output-panel {
            background: white;
            padding: 0;
        }
        
        .output-header {
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .output-content {
            padding: 40px;
            max-height: 800px;
            overflow-y: auto;
            line-height: 1.8;
        }
        
        .output-content h1 {
            color: #2c3e50;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }
        
        .output-content h2 {
            color: #667eea;
            margin: 30px 0 20px 0;
            font-size: 1.8rem;
        }
        
        .output-content p {
            color: #444;
            margin-bottom: 20px;
            text-align: justify;
        }
        
        .empty-state {
            text-align: center;
            padding: 100px 20px;
            color: #999;
        }
        
        .loading {
            text-align: center;
            padding: 100px 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: #fee;
            color: #c00;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .copy-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        
        .copy-btn:hover {
            background: #218838;
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
            <p>Upload your documents and generate professional investor pitches</p>
        </div>
        
        <div class="content">
            <div class="input-panel">
                <h2 style="margin-bottom: 25px; color: #333;">Pitch Information</h2>
                
                <!-- File Upload -->
                <div class="upload-zone" id="uploadZone">
                    <div style="font-size: 3rem; margin-bottom: 10px;">📁</div>
                    <div style="font-weight: 600; margin-bottom: 5px;">Drop files here or click to browse</div>
                    <div style="color: #666; font-size: 0.9rem;">PDF, Word, or text files with your pitch content</div>
                </div>
                <input type="file" id="fileInput" multiple accept=".pdf,.txt,.doc,.docx" style="display: none;">
                
                <div id="fileList" class="file-list"></div>
                
                <!-- Form Fields -->
                <div class="form-group">
                    <label>Company Name *</label>
                    <input type="text" id="companyName" placeholder="e.g., TechVentures Inc." required>
                </div>
                
                <div class="form-group">
                    <label>Industry *</label>
                    <input type="text" id="industry" placeholder="e.g., B2B SaaS, Fintech, Healthcare" required>
                </div>
                
                <div class="form-group">
                    <label>Problem You Solve *</label>
                    <textarea id="problem" placeholder="What specific problem does your company solve?" required></textarea>
                </div>
                
                <div class="form-group">
                    <label>Your Solution *</label>
                    <textarea id="solution" placeholder="How does your product/service solve this problem?" required></textarea>
                </div>
                
                <div class="form-group">
                    <label>Funding Stage</label>
                    <select id="fundingStage">
                        <option value="pre-seed">Pre-Seed ($500K-$1M)</option>
                        <option value="seed" selected>Seed ($2M-$3M)</option>
                        <option value="series-a">Series A ($10M-$15M)</option>
                        <option value="series-b">Series B ($30M-$50M)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Current Traction</label>
                    <input type="text" id="traction" placeholder="e.g., 100 customers, $1M ARR, 50% MoM growth">
                </div>
                
                <button class="generate-btn" id="generateBtn" onclick="generatePitch()">
                    Generate Sales Pitch
                </button>
            </div>
            
            <div class="output-panel">
                <div class="output-header">
                    <h2 style="margin: 0; color: #333;">Generated Pitch</h2>
                    <button class="copy-btn" id="copyBtn" style="display: none;" onclick="copyPitch()">
                        📋 Copy to Clipboard
                    </button>
                </div>
                <div class="output-content" id="output">
                    <div class="empty-state">
                        <h3>Your pitch will appear here</h3>
                        <p>Fill in your company details and click Generate</p>
                        <p style="margin-top: 20px; color: #667eea;">💡 Tip: Upload existing pitch decks or business plans for better results</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let uploadedFiles = [];
        
        // Get elements
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        const fileList = document.getElementById('fileList');
        const generateBtn = document.getElementById('generateBtn');
        const output = document.getElementById('output');
        const copyBtn = document.getElementById('copyBtn');
        
        // Upload zone click
        uploadZone.addEventListener('click', () => fileInput.click());
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });
        
        // Drag and drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragging');
        });
        
        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragging');
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragging');
            handleFiles(e.dataTransfer.files);
        });
        
        // Prevent default drag on document
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => e.preventDefault());
        
        // Handle files
        function handleFiles(files) {
            for (let file of files) {
                // Check file type
                const validTypes = ['application/pdf', 'text/plain', 'application/msword', 
                                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
                if (!validTypes.includes(file.type) && !file.name.endsWith('.txt')) {
                    alert(`Invalid file type: ${file.name}`);
                    continue;
                }
                
                // Check size (10MB max)
                if (file.size > 10 * 1024 * 1024) {
                    alert(`File too large: ${file.name} (max 10MB)`);
                    continue;
                }
                
                uploadedFiles.push(file);
            }
            updateFileList();
        }
        
        // Update file list
        function updateFileList() {
            if (uploadedFiles.length === 0) {
                fileList.innerHTML = '';
                return;
            }
            
            fileList.innerHTML = uploadedFiles.map((file, idx) => `
                <div class="file-item">
                    <span class="file-name">📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)</span>
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
            // Get form values
            const companyName = document.getElementById('companyName').value.trim();
            const industry = document.getElementById('industry').value.trim();
            const problem = document.getElementById('problem').value.trim();
            const solution = document.getElementById('solution').value.trim();
            const fundingStage = document.getElementById('fundingStage').value;
            const traction = document.getElementById('traction').value.trim();
            
            // Validate
            if (!companyName || !industry || !problem || !solution) {
                alert('Please fill in all required fields');
                return;
            }
            
            // UI feedback
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';
            output.innerHTML = '<div class="loading"><div class="spinner"></div><p>Creating your pitch...</p></div>';
            copyBtn.style.display = 'none';
            
            // Prepare form data
            const formData = new FormData();
            formData.append('company_name', companyName);
            formData.append('industry', industry);
            formData.append('problem', problem);
            formData.append('solution', solution);
            formData.append('funding_stage', fundingStage);
            formData.append('traction', traction);
            
            // Add files
            uploadedFiles.forEach(file => {
                formData.append('files', file);
            });
            
            try {
                const response = await fetch('/api/generate-pitch', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok && !data.error) {
                    displayPitch(data);
                    copyBtn.style.display = 'block';
                } else {
                    output.innerHTML = `<div class="error">
                        <h3>Error Generating Pitch</h3>
                        <p>${data.error || 'Unknown error occurred'}</p>
                    </div>`;
                }
            } catch (error) {
                console.error('Error:', error);
                output.innerHTML = `<div class="error">
                    <h3>Connection Error</h3>
                    <p>Failed to connect to server. Please try again.</p>
                </div>`;
            } finally {
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate Sales Pitch';
            }
        }
        
        // Display pitch
        function displayPitch(data) {
            let html = `<h1>${data.company_name}</h1>`;
            
            if (data.executive_summary) {
                html += '<h2>Executive Summary</h2>';
                html += data.executive_summary.split('\n').map(p => `<p>${p}</p>`).join('');
            }
            
            if (data.opportunity) {
                html += '<h2>The Opportunity</h2>';
                html += data.opportunity.split('\n').map(p => `<p>${p}</p>`).join('');
            }
            
            if (data.why_us) {
                html += '<h2>Why ' + data.company_name + '</h2>';
                html += data.why_us.split('\n').map(p => `<p>${p}</p>`).join('');
            }
            
            output.innerHTML = html;
        }
        
        // Copy to clipboard
        function copyPitch() {
            const text = output.innerText;
            navigator.clipboard.writeText(text).then(() => {
                const btn = document.getElementById('copyBtn');
                const originalText = btn.textContent;
                btn.textContent = '✅ Copied!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            });
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
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "openai": "connected",
        "model": OPENAI_MODEL
    })

@app.route('/api/generate-pitch', methods=['POST'])
def generate_pitch():
    """Generate pitch with AI using uploaded files"""
    try:
        # Get form data
        company_name = request.form.get('company_name', '').strip()
        industry = request.form.get('industry', '').strip()
        problem = request.form.get('problem', '').strip()
        solution = request.form.get('solution', '').strip()
        funding_stage = request.form.get('funding_stage', 'seed')
        traction = request.form.get('traction', '').strip()
        
        # Validate required fields
        if not all([company_name, industry, problem, solution]):
            return jsonify({"error": "Missing required fields"}), 400
        
        logger.info(f"Generating pitch for {company_name}")
        
        # Process uploaded files
        document_content = ""
        if 'files' in request.files:
            files = request.files.getlist('files')
            logger.info(f"Processing {len(files)} uploaded files")
            
            for file in files:
                if file and file.filename:
                    logger.info(f"Reading file: {file.filename}")
                    text = extract_text_from_file(file)
                    if text:
                        document_content += f"\n\n=== Content from {file.filename} ===\n{text}\n"
        
        # Generate the pitch
        pitch = create_pitch_with_ai(
            company_name=company_name,
            industry=industry,
            problem=problem,
            solution=solution,
            funding_stage=funding_stage,
            traction=traction,
            document_content=document_content
        )
        
        return jsonify(pitch)
        
    except Exception as e:
        logger.error(f"Error generating pitch: {str(e)}")
        return jsonify({"error": str(e)}), 500

def extract_text_from_file(file):
    """Extract text content from uploaded file"""
    try:
        filename = file.filename.lower()
        file_content = file.read()
        
        # PDF files
        if filename.endswith('.pdf') and PyPDF2:
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                text = ""
                for page_num, page in enumerate(pdf_reader.pages[:20]):  # Limit to 20 pages
                    text += page.extract_text() + "\n"
                logger.info(f"Extracted {len(text)} characters from PDF")
                return text[:10000]  # Limit to 10k chars
            except Exception as e:
                logger.error(f"PDF extraction failed: {e}")
                return ""
        
        # Text files
        elif filename.endswith('.txt'):
            text = file_content.decode('utf-8', errors='ignore')
            logger.info(f"Extracted {len(text)} characters from TXT")
            return text[:10000]
        
        # Word files - just try to read as text
        else:
            try:
                text = file_content.decode('utf-8', errors='ignore')
                return text[:10000]
            except:
                return ""
                
    except Exception as e:
        logger.error(f"File extraction error: {e}")
        return ""

def create_pitch_with_ai(company_name, industry, problem, solution, funding_stage, traction, document_content):
    """Generate pitch using OpenAI"""
    
    # Determine funding amount
    funding_amounts = {
        "pre-seed": "$500K-$1M",
        "seed": "$2-3M",
        "series-a": "$10-15M",
        "series-b": "$30-50M"
    }
    funding_amount = funding_amounts.get(funding_stage, "$5M")
    
    # Build the prompt
    prompt = f"""
    You are a world-class venture capital pitch consultant. Create an exceptional 2-3 page investor pitch.
    
    COMPANY INFORMATION:
    - Company: {company_name}
    - Industry: {industry}
    - Problem: {problem}
    - Solution: {solution}
    - Stage: {funding_stage}
    - Traction: {traction if traction else "Early stage"}
    - Funding Sought: {funding_amount}
    
    UPLOADED DOCUMENT CONTENT:
    {document_content[:5000] if document_content else "No documents uploaded"}
    
    INSTRUCTIONS:
    1. If documents were uploaded, incorporate ALL specific metrics, data, and information from them
    2. Use real numbers from the documents - don't make up different ones
    3. Be specific and detailed - this needs to convince real investors
    4. If no documents provided, create realistic metrics based on {industry} standards
    
    CREATE EXACTLY THESE 3 SECTIONS:
    
    EXECUTIVE SUMMARY (300 words):
    - Opening: One powerful sentence describing what {company_name} does
    - Problem: The urgent problem with market size and impact
    - Solution: How the solution works and why it's 10x better
    - Traction: Specific metrics (use from documents if provided)
    - Market: TAM with dollar amount and growth rate
    - Team: Brief expertise mention
    - Ask: {funding_amount} and what it achieves
    
    THE OPPORTUNITY (500 words):
    Structure as:
    - THE PROBLEM: Detailed pain points, costs, market failures
    - OUR SOLUTION: How it works, key features, ROI for customers
    - MARKET SIZE: TAM, SAM, SOM with specific numbers
    - BUSINESS MODEL: Revenue model, pricing, unit economics
    - COMPETITIVE ADVANTAGE: What makes this defensible
    
    WHY {company_name.upper()} (300 words):
    - TRACTION: Current metrics, growth rate, customers
    - TEAM: Relevant backgrounds and expertise
    - USE OF FUNDS: Specific allocation of {funding_amount}
    - MILESTONES: 18-month targets with metrics
    - VISION: Path to market leadership
    
    Use specific numbers, percentages, and examples throughout.
    Make it compelling and investor-ready.
    
    Return as JSON with keys: executive_summary, opportunity, why_us, company_name
    """
    
    try:
        logger.info(f"Calling OpenAI API with model {OPENAI_MODEL}")
        
        response = ai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert pitch consultant. Create detailed, compelling, data-driven pitches. Always use specific information from uploaded documents when provided."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result['company_name'] = company_name
        
        logger.info("Successfully generated pitch with AI")
        return result
        
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise Exception(f"AI generation failed: {str(e)}")

if __name__ == '__main__':
    print(f"""
    =====================================
    🚀 AI Sales Pitch Generator
    =====================================
    Status: Ready
    Port: {PORT}
    Model: {OPENAI_MODEL}
    API: Connected ✅
    
    Visit: http://localhost:{PORT}
    =====================================
    """)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)