#!/usr/bin/env python3
"""
AI Sales Pitch Generator - Clean Rewrite
Simple, working 2-3 page pitch generator with file upload
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
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')  # Default to GPT-4
PORT = int(os.getenv('PORT', 5001))

# Initialize OpenAI
ai_client = None
if OPENAI_API_KEY and OpenAI:
    try:
        ai_client = OpenAI(api_key=OPENAI_API_KEY)
        # Test the API key with a simple request
        test_response = ai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use cheaper model for test
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        logger.info(f"✅ OpenAI initialized successfully with model: {OPENAI_MODEL}")
    except Exception as e:
        logger.error(f"❌ OpenAI initialization failed: {e}")
        ai_client = None
else:
    logger.error("❌ No OpenAI API key configured - set OPENAI_API_KEY in .env file")

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
        extracted_info = {
            "financials": "",
            "team_info": "",
            "product_details": "",
            "market_data": "",
            "competitive_analysis": ""
        }
        
        if 'files' in request.files:
            files = request.files.getlist('files')
            logger.info(f"Processing {len(files)} uploaded files")
            
            for file in files:
                if file and file.filename:
                    logger.info(f"Extracting content from: {file.filename}")
                    content = extract_file_content(file)
                    if content:
                        additional_context += f"\n\n--- Content from {file.filename} ---\n{content}\n"
                        
                        # Try to categorize the content
                        content_lower = content.lower()
                        if any(word in content_lower for word in ['revenue', 'arr', 'mrr', 'financial', 'profit', 'margin']):
                            extracted_info["financials"] += content + "\n"
                        if any(word in content_lower for word in ['team', 'founder', 'ceo', 'cto', 'experience']):
                            extracted_info["team_info"] += content + "\n"
                        if any(word in content_lower for word in ['product', 'feature', 'technology', 'platform']):
                            extracted_info["product_details"] += content + "\n"
                        if any(word in content_lower for word in ['market', 'tam', 'industry', 'growth']):
                            extracted_info["market_data"] += content + "\n"
                        if any(word in content_lower for word in ['competitor', 'competition', 'alternative']):
                            extracted_info["competitive_analysis"] += content + "\n"
        
        # If we have file content, extract key information using AI
        if additional_context:
            logger.info(f"Extracted {len(additional_context)} characters from files")
            
            # First, extract structured data from the files
            if ai_client:
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
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    
                    extracted_data = json.loads(extraction_response.choices[0].message.content)
                    logger.info(f"Successfully extracted structured data from files")
                    
                    # Merge extracted data with form inputs
                    if extracted_data.get('revenue_metrics'):
                        traction = f"{traction} {extracted_data['revenue_metrics']}"
                    
                    # Pass the extracted data to the pitch generator
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
                    
                except Exception as e:
                    logger.error(f"Failed to extract data from files: {e}")
                    # Fall back to basic generation
                    pitch = generate_pitch_content(
                        company_name,
                        industry,
                        problem,
                        solution,
                        funding_stage,
                        traction,
                        additional_context
                    )
            else:
                pitch = generate_pitch_content(
                    company_name,
                    industry,
                    problem,
                    solution,
                    funding_stage,
                    traction,
                    additional_context
                )
        else:
            # No files, generate normally
            pitch = generate_pitch_content(
                company_name,
                industry,
                problem,
                solution,
                funding_stage,
                traction
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
                text += page.extract_text() + "\n"
            return text[:5000]  # Increase limit for better extraction
            
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
                if extracted_data.get('company_description'):
                    file_context += f"\nCompany Description from docs: {extracted_data['company_description']}"
                if extracted_data.get('revenue_metrics'):
                    file_context += f"\nRevenue/Metrics from docs: {extracted_data['revenue_metrics']}"
                if extracted_data.get('team_details'):
                    file_context += f"\nTeam Info from docs: {extracted_data['team_details']}"
                if extracted_data.get('product_features'):
                    file_context += f"\nProduct Features from docs: {extracted_data['product_features']}"
                if extracted_data.get('market_size'):
                    file_context += f"\nMarket Data from docs: {extracted_data['market_size']}"
                if extracted_data.get('competitors'):
                    file_context += f"\nCompetitors from docs: {extracted_data['competitors']}"
                if extracted_data.get('achievements'):
                    file_context += f"\nAchievements from docs: {extracted_data['achievements']}"
                if extracted_data.get('key_metrics'):
                    file_context += f"\nKey Metrics from docs: {extracted_data['key_metrics']}"
                    
            # Much more detailed prompt that uses the file content
            prompt = f"""
            You are a top Silicon Valley pitch consultant who has helped raise over $1B in funding.
            Create a compelling, professional 2-3 page sales pitch that incorporates ALL the information from their uploaded documents.
            
            COMPANY DETAILS FROM FORM:
            Company: {company_name}
            Industry: {industry}
            Problem: {problem}
            Solution: {solution}
            Funding Stage: {funding_stage}
            Current Traction: {traction if traction else "Early stage"}
            
            CRITICAL INFORMATION EXTRACTED FROM THEIR DOCUMENTS:
            {file_context}
            
            RAW DOCUMENT CONTENT (USE THIS FOR ADDITIONAL CONTEXT):
            {context[:3000]}
            
            IMPORTANT: You MUST incorporate the specific information from their documents above. Use their actual metrics, team info, product details, etc.
            Don't make up numbers if they provided real ones in the documents.
            
            Create a pitch with EXACTLY these 3 sections:
            
            1. EXECUTIVE SUMMARY (250-300 words)
            - Start with what {company_name} does (use their description from docs if provided)
            - The problem (incorporate any market data from their docs)
            - The solution (use specific product features from their docs)
            - Traction (USE THEIR ACTUAL METRICS from docs: {extracted_data.get('revenue_metrics') if extracted_data else traction})
            - Market size (use their TAM data if provided in docs)
            - Funding ask: {funding_amount} for specific milestones
            - Include their actual achievements from docs
            
            2. THE OPPORTUNITY (400-450 words)
            - Problem: Use specific pain points from their documents
            - Solution: Detail their actual product features from docs
            - Market: Use their market research if provided
            - Business Model: Reference their actual pricing/model from docs
            - Competition: Mention specific competitors from their docs
            
            3. WHY {company_name.upper()} (250-300 words)
            - Traction: Use their ACTUAL metrics from the documents
            - Team: Include ACTUAL team info from their docs (don't make up backgrounds)
            - The Ask: {funding_amount} with use of funds from their docs if mentioned
            - Include their real partnerships, customers, achievements
            
            BE SPECIFIC. USE THEIR REAL DATA. If they uploaded a pitch deck, use those exact numbers and facts.
            
            Return as JSON with keys: executive_summary, opportunity, why_us, company_name
            """
            
            response = ai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a world-class pitch expert. Always use the specific data and information provided in the uploaded documents. Never ignore document content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result['company_name'] = company_name
            logger.info("Successfully generated pitch incorporating document content")
            return result
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
    """Generate pitch using AI or template"""
    
    # Determine funding amount based on stage
    funding_amounts = {
        "seed": "$2-3M",
        "series-a": "$10-15M", 
        "series-b": "$30-50M"
    }
    funding_amount = funding_amounts.get(funding_stage, "$5M")
    
    if ai_client:
        try:
            # Much more detailed prompt for quality output
            prompt = f"""
            You are a top Silicon Valley pitch consultant who has helped raise over $1B in funding.
            Create a compelling, professional 2-3 page sales pitch that will actually convince investors.
            
            COMPANY DETAILS:
            Company: {company_name}
            Industry: {industry}
            Problem: {problem}
            Solution: {solution}
            Funding Stage: {funding_stage}
            Current Traction: {traction if traction else "Early stage, pre-revenue"}
            
            ADDITIONAL CONTEXT FROM UPLOADED DOCUMENTS:
            {context[:2000]}
            
            Create a pitch with EXACTLY these 3 sections:
            
            1. EXECUTIVE SUMMARY (250-300 words)
            Start with a powerful hook sentence about what {company_name} does.
            Then cover:
            - The urgent problem in {industry} that costs companies millions
            - Your unique solution and why it's 10x better than alternatives
            - Current traction: {traction if traction else "pilot customers and early validation"}
            - Market size: Research and provide realistic TAM for {industry}
            - Funding ask: Raising {funding_amount} to achieve specific milestones
            - Include 2-3 impressive metrics or achievements
            
            2. THE OPPORTUNITY (400-450 words)
            
            THE PROBLEM:
            - Expand on the problem with specific pain points and costs
            - Include statistics about the {industry} market
            - Explain why existing solutions fail
            - Quantify the cost of not solving this problem
            
            OUR SOLUTION:
            - Detailed explanation of how {solution} works
            - 3-4 key features that make it unique
            - Specific benefits and ROI for customers
            - Why this is possible now (technology, market, regulatory changes)
            
            MARKET OPPORTUNITY:
            - TAM: Total addressable market for {industry} (use realistic numbers)
            - SAM: Serviceable addressable market 
            - SOM: Serviceable obtainable market (1-2% of TAM)
            - Growth rate and market drivers
            - Target customer profile and segments
            
            BUSINESS MODEL:
            - How you make money (SaaS, marketplace, transaction fees, etc.)
            - Pricing strategy and average contract values
            - Unit economics (CAC, LTV, gross margins)
            - Path to profitability
            
            3. WHY {company_name.upper()} (250-300 words)
            
            TRACTION & VALIDATION:
            - Current metrics: {traction if traction else "5 pilot customers, 50+ on waitlist"}
            - Growth rate and momentum
            - Customer testimonials or case studies
            - Key partnerships or integrations
            
            OUR TEAM:
            - Founders with deep {industry} expertise (make up realistic backgrounds)
            - Key advisors from successful companies
            - Why this team is uniquely positioned to win
            
            THE ASK:
            - Raising {funding_amount} {funding_stage} round
            - Specific use of funds (product: 40%, sales: 35%, team: 25%)
            - 18-month milestones:
              • 10x revenue growth to $10M ARR
              • Expand to 3 new markets
              • Launch enterprise product
              • Build team to 50 people
            - Path to next round and eventual exit strategy
            
            End with a compelling call to action about joining the journey.
            
            IMPORTANT:
            - Use specific numbers, percentages, and metrics throughout
            - Include industry-specific terminology for {industry}
            - Write in confident, professional tone
            - Make it feel real with concrete details
            - Don't use generic platitudes - be specific
            - Include actual market data and statistics where possible
            
            Return as JSON with keys: executive_summary, opportunity, why_us, company_name
            """
            
            response = ai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a world-class venture capital pitch expert. Create detailed, compelling, realistic pitches with specific metrics and data. Make it feel like a real company with real traction."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Slightly higher for creativity
                max_tokens=3000,  # Allow longer responses
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result['company_name'] = company_name
            return result
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
    
    # Much better fallback template (without broken placeholders)
    logger.warning("Using fallback template - AI not available or failed")
    
    # Parse any numbers from the uploaded context
    arr_match = re.search(r'\$?([\d\.]+[MK]?) (?:in )?ARR', context, re.IGNORECASE) if context else None
    actual_arr = arr_match.group(1) if arr_match else "$500K"
    
    customers_match = re.search(r'(\d+)\s+(?:enterprise\s+)?customers', context, re.IGNORECASE) if context else None
    actual_customers = customers_match.group(1) if customers_match else "25"
    
    return {
        "company_name": company_name,
        "executive_summary": f"""
{company_name} is transforming the {industry} industry by solving the critical challenge of {problem}. Our innovative approach - {solution} - delivers unprecedented value to enterprises seeking competitive advantage in an increasingly complex market.

Since our launch, we've achieved {traction if traction else f'{actual_arr} in annual recurring revenue with {actual_customers} enterprise customers'}, demonstrating strong product-market fit and rapid market adoption. Our solution addresses a multi-billion dollar market opportunity in {industry}, with enterprises spending billions annually on inadequate solutions.

We're raising {funding_amount} in {funding_stage} funding to accelerate our growth trajectory. This investment will fuel product innovation, sales expansion, and operational scaling as we capitalize on our first-mover advantage in this rapidly evolving market.
        """.strip(),
        
        "opportunity": f"""
THE PROBLEM:
{problem} represents one of the most significant challenges facing the {industry} sector today. Organizations struggle with inefficient processes, fragmented solutions, and inability to scale effectively. This results in millions in lost revenue, decreased productivity, and competitive disadvantage. Current solutions fail to address the root cause, offering only partial fixes that create more complexity.

OUR SOLUTION:
{company_name}'s approach is fundamentally different. {solution} - this isn't just an incremental improvement, but a complete reimagining of how {industry} companies operate. Our platform delivers immediate value through automated workflows, intelligent insights, and seamless integration with existing systems. Customers report dramatic improvements in efficiency, cost reduction, and strategic decision-making capability.

MARKET OPPORTUNITY:
The {industry} market is experiencing unprecedented growth, driven by digital transformation, changing customer expectations, and regulatory requirements. Conservative estimates place the total addressable market at tens of billions, with double-digit annual growth rates. Our initial focus on enterprise customers represents a multi-billion dollar opportunity, with clear expansion paths into adjacent markets and international regions.

BUSINESS MODEL:
We've developed a scalable SaaS model with strong unit economics. Our tiered pricing structure serves organizations from mid-market to enterprise, with average contract values growing consistently. High gross margins and increasing customer lifetime value demonstrate the sustainability and scalability of our business model.
        """.strip(),
        
        "why_us": f"""
TRACTION & VALIDATION:
Our growth trajectory validates the market need and our solution's effectiveness. {traction if traction else f'With {actual_arr} in ARR and {actual_customers} customers, including Fortune 500 companies'}, we've proven our ability to win and retain enterprise accounts. Customer success stories include dramatic ROI, operational improvements, and competitive advantages gained through our platform.

OUR TEAM:
{company_name} is led by a team with deep expertise in {industry} and proven track records of building successful companies. Our leadership combines technical innovation with go-to-market excellence, supported by advisors and investors who've built category-defining companies. This is not our first venture - we've successfully scaled companies, navigated complex markets, and delivered exceptional returns.

THE ASK:
We're raising {funding_amount} to accelerate our momentum. Investment will be strategically deployed across three key areas: Product development to maintain our technical advantage, Sales and marketing to capture market share, and Operations to support our scaling needs. Our roadmap includes expanding our enterprise features, entering new markets, and building the team to support 10x growth over the next 18 months.

This is an opportunity to invest in the future of {industry}. With proven traction, a massive market opportunity, and an exceptional team, {company_name} is positioned to become the category-defining company in this space.
        """.strip()
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