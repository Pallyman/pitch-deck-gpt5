#!/usr/bin/env python3
"""
AI Sales Pitch Generator - Fixed Version
Now with proper model validation and clear error messages
"""

import os
import json
import logging
import io
import re
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv

# OpenAI
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: OpenAI not installed. Run: pip install openai")
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

# Config with validation
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # Default to a VALID model
PORT = int(os.getenv('PORT', 5001))

# Valid OpenAI models (including GPT-5 as of Aug 2025!)
VALID_MODELS = [
    'gpt-5', 'gpt-5-mini', 'gpt-5-nano',  # New GPT-5 models!
    'gpt-5-2025-08-07',  # Date-versioned GPT-5
    'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 
    'gpt-3.5-turbo', 'gpt-3.5-turbo-16k'
]

# Validate model
if OPENAI_MODEL not in VALID_MODELS:
    logger.error(f"❌ Invalid model '{OPENAI_MODEL}'. Valid models: {', '.join(VALID_MODELS)}")
    logger.warning(f"⚠️ Defaulting to 'gpt-4o-mini'")
    OPENAI_MODEL = 'gpt-4o-mini'

# Initialize OpenAI with better error handling
ai_client = None
ai_status = "Not configured"

if not OPENAI_API_KEY:
    ai_status = "Missing API key - set OPENAI_API_KEY in environment"
    logger.error(f"❌ {ai_status}")
elif not OpenAI:
    ai_status = "OpenAI library not installed"
    logger.error(f"❌ {ai_status}")
else:
    try:
        ai_client = OpenAI(api_key=OPENAI_API_KEY)
        # Test with the ACTUAL model we'll use
        test_response = ai_client.chat.completions.create(
            model=OPENAI_MODEL,  # Use the actual model
            messages=[{"role": "user", "content": "test"}],
            max_completion_tokens=5  # Use correct parameter name for GPT-5
        )
        ai_status = f"Connected (using {OPENAI_MODEL})"
        logger.info(f"✅ OpenAI initialized successfully with model: {OPENAI_MODEL}")
    except Exception as e:
        ai_status = f"Failed: {str(e)}"
        logger.error(f"❌ OpenAI initialization failed: {e}")
        logger.error(f"   Check your API key and model name ({OPENAI_MODEL})")
        ai_client = None

# Main HTML page (keeping your original UI)
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
        
        .ai-status {
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 10px;
            font-size: 0.9rem;
        }
        
        .ai-status.connected {
            background: rgba(76, 175, 80, 0.3);
        }
        
        .ai-status.error {
            background: rgba(244, 67, 54, 0.3);
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
        
        .error-message {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
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
            <div class="ai-status" id="aiStatus">
                Checking AI connection...
            </div>
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
        
        // Check AI status on load
        fetch('/health')
            .then(res => res.json())
            .then(data => {
                const statusEl = document.getElementById('aiStatus');
                if (data.ai_available) {
                    statusEl.className = 'ai-status connected';
                    statusEl.textContent = '✅ AI Connected';
                } else {
                    statusEl.className = 'ai-status error';
                    statusEl.textContent = '⚠️ AI Not Available (using fallback)';
                }
            })
            .catch(() => {
                document.getElementById('aiStatus').textContent = '❌ Server Error';
            });
        
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
                    output.innerHTML = `
                        <div class="error-message">
                            <strong>Error:</strong> ${data.error}
                            ${data.details ? `<br><small>${data.details}</small>` : ''}
                        </div>
                    `;
                } else {
                    displayPitch(data);
                }
            } catch (error) {
                output.innerHTML = '<div class="error-message">Error connecting to server</div>';
            }
            
            btn.disabled = false;
            btn.textContent = 'Generate Sales Pitch';
        }
        
        // Display pitch
        function displayPitch(data) {
            const output = document.getElementById('output');
            
            let html = '<h1>' + (data.company_name || 'Sales Pitch') + '</h1>';
            
            if (data.generation_method) {
                html += `<p style="color: #667eea; font-size: 0.9rem;">Generated via: ${data.generation_method}</p>`;
            }
            
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
    """Health check with detailed status"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_available": ai_client is not None,
        "ai_status": ai_status,
        "model": OPENAI_MODEL if ai_client else None
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
        extracted_data = None
        
        if 'files' in request.files:
            files = request.files.getlist('files')
            logger.info(f"Processing {len(files)} uploaded files")
            
            for file in files:
                if file and file.filename:
                    logger.info(f"Extracting content from: {file.filename}")
                    content = extract_file_content(file)
                    if content:
                        additional_context += f"\n\n--- Content from {file.filename} ---\n{content}\n"
        
        # Extract structured data from files if AI is available
        if additional_context and ai_client:
            logger.info(f"Extracting structured data from {len(additional_context)} chars")
            try:
                extraction_prompt = f"""
                Extract key business information from these documents:
                
                {additional_context[:4000]}
                
                Extract and return as JSON:
                - company_description: Detailed description of what the company does
                - revenue_metrics: Any revenue, ARR, MRR, growth rates mentioned
                - team_details: Information about founders and team
                - product_features: Key product features and capabilities
                - market_size: TAM, SAM, SOM if mentioned
                - competitors: Any competitors mentioned
                - achievements: Awards, partnerships, milestones
                - financial_projections: Future revenue/growth projections
                - use_of_funds: How they plan to use investment
                - key_metrics: Other important metrics (users, NPS, etc.)
                
                If not found, leave empty. Be thorough.
                """
                
                extraction_response = ai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "Extract specific business data from documents."},
                        {"role": "user", "content": extraction_prompt}
                    ],
                    temperature=1,  # GPT-5 only supports default temperature
                    response_format={"type": "json_object"}
                )
                
                extracted_data = json.loads(extraction_response.choices[0].message.content)
                logger.info(f"Successfully extracted structured data from files")
                
            except Exception as e:
                logger.error(f"Failed to extract data from files: {e}")
        
        # Generate the pitch
        pitch = generate_pitch_content(
            company_name,
            industry,
            problem,
            solution,
            funding_stage,
            traction,
            additional_context,
            extracted_data
        )
        
        return jsonify(pitch)
        
    except Exception as e:
        logger.error(f"Error in /api/generate: {e}")
        return jsonify({
            "error": "Failed to generate pitch",
            "details": str(e) if app.debug else None
        }), 500

def extract_file_content(file):
    """Extract text from uploaded file"""
    try:
        filename = file.filename.lower()
        file_content = file.read()
        
        if filename.endswith('.pdf') and PyPDF2:
            pdf = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            return text[:5000]
            
        elif filename.endswith('.txt'):
            return file_content.decode('utf-8', errors='ignore')[:5000]
            
        elif filename.endswith(('.doc', '.docx')) and Document:
            doc = Document(io.BytesIO(file_content))
            text = "\n".join([p.text for p in doc.paragraphs])
            return text[:5000]
            
    except Exception as e:
        logger.error(f"File extraction error: {e}")
    
    return ""

def generate_pitch_content(company_name, industry, problem, solution, funding_stage, traction, context="", extracted_data=None):
    """Generate pitch using AI with file context"""
    
    # Determine funding amount based on stage
    funding_amounts = {
        "seed": "$2-3M",
        "series-a": "$10-15M", 
        "series-b": "$30-50M"
    }
    funding_amount = funding_amounts.get(funding_stage, "$5M")
    
    if ai_client:
        try:
            # Build context from extracted data
            file_context = ""
            if extracted_data:
                for key, value in extracted_data.items():
                    if value:
                        file_context += f"\n{key.replace('_', ' ').title()}: {value}"
            
            prompt = f"""
            You are a top Silicon Valley pitch consultant who has helped raise over $1B in funding.
            Create a compelling, professional 2-3 page sales pitch.
            
            COMPANY DETAILS:
            Company: {company_name}
            Industry: {industry}
            Problem: {problem}
            Solution: {solution}
            Funding Stage: {funding_stage}
            Current Traction: {traction if traction else "Early stage"}
            
            {'EXTRACTED FROM DOCUMENTS:' + file_context if file_context else ''}
            
            {'RAW DOCUMENT CONTENT:' + context[:2000] if context else ''}
            
            Create a pitch with EXACTLY these 3 sections:
            
            1. EXECUTIVE SUMMARY (250-300 words)
            - What {company_name} does
            - The problem and market opportunity
            - The solution and why it's unique
            - Current traction (use actual metrics from docs if provided)
            - Funding ask: {funding_amount}
            
            2. THE OPPORTUNITY (400-450 words)
            - Problem details with market pain points
            - Solution with specific features
            - Market size and growth
            - Business model and unit economics
            - Competitive landscape
            
            3. WHY {company_name.upper()} (250-300 words)
            - Traction and validation
            - Team expertise
            - Use of funds
            - Path to success
            
            Use specific numbers and metrics. Be compelling and professional.
            
            Return as JSON with keys: executive_summary, opportunity, why_us, company_name, generation_method
            """
            
            response = ai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a world-class pitch expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=1,  # GPT-5 only supports default temperature
                max_completion_tokens=3000,  # Changed from max_tokens
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result['company_name'] = company_name
            result['generation_method'] = f"AI ({OPENAI_MODEL})"
            logger.info(f"Successfully generated pitch using {OPENAI_MODEL}")
            return result
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            # Fall through to template
    
    # Fallback template
    logger.warning("Using fallback template - AI not available")
    
    return {
        "company_name": company_name,
        "generation_method": "Template (AI unavailable)",
        "executive_summary": f"""
{company_name} is transforming the {industry} industry by solving {problem}. 
Our solution - {solution} - delivers unprecedented value to enterprises.

Since launch, we've achieved {traction if traction else 'strong early traction'}, 
demonstrating product-market fit. The {industry} market represents a multi-billion 
dollar opportunity.

We're raising {funding_amount} in {funding_stage} funding to accelerate growth 
and capture market share.
        """.strip(),
        
        "opportunity": f"""
THE PROBLEM:
{problem} is a critical challenge in {industry}. Organizations struggle with 
inefficiency and lost revenue.

OUR SOLUTION:
{solution} provides a fundamentally better approach. We deliver immediate value 
through automation and insights.

MARKET OPPORTUNITY:
The {industry} market is experiencing rapid growth. Our addressable market 
exceeds several billion dollars.

BUSINESS MODEL:
We operate a scalable SaaS model with strong unit economics and growing 
customer lifetime value.
        """.strip(),
        
        "why_us": f"""
TRACTION:
{traction if traction else 'Early customer validation and growing pipeline'}.

TEAM:
Led by experienced operators with deep {industry} expertise.

THE ASK:
Raising {funding_amount} to expand product, grow sales, and scale operations.
{company_name} is positioned to become the leader in this space.
        """.strip()
    }

if __name__ == '__main__':
    print(f"""
    ========================================
    AI Sales Pitch Generator
    ========================================
    Starting on port {PORT}
    AI Status: {ai_status}
    Model: {OPENAI_MODEL if ai_client else 'N/A'}
    
    Visit: http://localhost:{PORT}
    ========================================
    """)
    
    app.run(host='0.0.0.0', port=PORT, debug=True)