#!/usr/bin/env python3
"""
AI-Powered Sales Pitch Generator
Clean, focused backend for generating 2-3 page sales pitches
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["*"])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-5-2025-08-07')
    USE_BUDGET_MODEL = os.getenv('USE_BUDGET_MODEL', 'false').lower() == 'true'
    PORT = int(os.getenv('PORT', 5001))

# Initialize OpenAI client
ai_client = None
if Config.OPENAI_API_KEY:
    try:
        ai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        logger.info(f"✅ OpenAI client initialized with model: {Config.OPENAI_MODEL}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenAI: {e}")
else:
    logger.warning("⚠️ No OpenAI API key - using mock responses")

# HTML Template for the frontend
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Sales Pitch Generator - 2-Page Professional Pitches</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
            animation: fadeIn 0.8s ease;
        }
        
        .header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.3rem;
            opacity: 0.95;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 450px 1fr;
            gap: 30px;
            animation: slideUp 0.8s ease;
        }
        
        .input-panel {
            background: white;
            border-radius: 15px;
            padding: 35px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            height: fit-content;
        }
        
        .input-panel h2 {
            color: #1e3c72;
            margin-bottom: 25px;
            font-size: 1.8rem;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
            font-size: 0.95rem;
        }
        
        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s;
            font-family: inherit;
        }
        
        .form-group input:focus,
        .form-group textarea:focus,
        .form-group select:focus {
            outline: none;
            border-color: #2a5298;
            box-shadow: 0 0 0 3px rgba(42, 82, 152, 0.1);
        }
        
        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        .required {
            color: #e74c3c;
        }
        
        .generate-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.2rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(46, 204, 113, 0.4);
        }
        
        .generate-btn:disabled {
            background: #95a5a6;
            cursor: not-allowed;
            transform: none;
        }
        
        .output-panel {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        
        .output-header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .output-header h2 {
            font-size: 1.5rem;
        }
        
        .action-buttons {
            display: flex;
            gap: 10px;
        }
        
        .action-btn {
            padding: 8px 16px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }
        
        .action-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .output-content {
            padding: 40px;
            min-height: 600px;
            max-height: 800px;
            overflow-y: auto;
            background: #fafafa;
        }
        
        .pitch-document {
            background: white;
            padding: 50px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            line-height: 1.8;
            font-size: 1.05rem;
        }
        
        .pitch-document h1 {
            color: #1e3c72;
            font-size: 2.5rem;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #2a5298;
        }
        
        .pitch-document h2 {
            color: #2a5298;
            font-size: 1.8rem;
            margin-top: 35px;
            margin-bottom: 20px;
        }
        
        .pitch-document h3 {
            color: #34495e;
            font-size: 1.4rem;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        
        .pitch-document p {
            color: #2c3e50;
            margin-bottom: 18px;
            text-align: justify;
        }
        
        .pitch-document ul {
            margin: 20px 0;
            padding-left: 30px;
        }
        
        .pitch-document li {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .pitch-document .highlight {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            padding: 20px;
            border-left: 4px solid #f39c12;
            margin: 20px 0;
            border-radius: 5px;
        }
        
        .empty-state {
            text-align: center;
            padding: 100px 20px;
            color: #95a5a6;
        }
        
        .empty-state h3 {
            font-size: 1.8rem;
            margin-bottom: 15px;
        }
        
        .loading {
            text-align: center;
            padding: 100px 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #2a5298;
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
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @media (max-width: 1024px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
        
        @media print {
            body {
                background: white;
            }
            .container {
                max-width: 100%;
            }
            .header, .input-panel, .output-header {
                display: none;
            }
            .output-panel {
                box-shadow: none;
            }
            .pitch-document {
                box-shadow: none;
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AI Sales Pitch Generator</h1>
            <p>Create compelling 2-3 page investor pitches powered by GPT-5</p>
        </div>
        
        <div class="main-grid">
            <div class="input-panel">
                <h2>Pitch Details</h2>
                <form id="pitchForm">
                    <div class="form-group">
                        <label>Company Name <span class="required">*</span></label>
                        <input type="text" id="companyName" placeholder="e.g., TechVentures Inc." required>
                    </div>
                    
                    <div class="form-group">
                        <label>Industry <span class="required">*</span></label>
                        <input type="text" id="industry" placeholder="e.g., B2B SaaS, Fintech, Healthcare" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Problem You Solve <span class="required">*</span></label>
                        <textarea id="problem" placeholder="Describe the specific problem your company solves..." required></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Your Solution <span class="required">*</span></label>
                        <textarea id="solution" placeholder="How does your product/service solve this problem?" required></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Funding Stage</label>
                        <select id="fundingStage">
                            <option value="pre-seed">Pre-Seed ($250K - $1M)</option>
                            <option value="seed" selected>Seed ($1M - $3M)</option>
                            <option value="series-a">Series A ($5M - $15M)</option>
                            <option value="series-b">Series B ($15M - $50M)</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Current Traction</label>
                        <input type="text" id="traction" placeholder="e.g., 50 customers, $100k MRR, 30% MoM growth">
                    </div>
                    
                    <button type="submit" class="generate-btn" id="generateBtn">
                        Generate Sales Pitch
                    </button>
                </form>
            </div>
            
            <div class="output-panel">
                <div class="output-header">
                    <h2>Generated Pitch</h2>
                    <div class="action-buttons" id="actionButtons" style="display: none;">
                        <button class="action-btn" onclick="copyPitch()">📋 Copy</button>
                        <button class="action-btn" onclick="printPitch()">🖨️ Print/PDF</button>
                    </div>
                </div>
                
                <div class="output-content" id="outputContent">
                    <div class="empty-state">
                        <h3>Your pitch will appear here</h3>
                        <p>Fill in your company details and click "Generate Sales Pitch"</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('pitchForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await generatePitch();
        });
        
        async function generatePitch() {
            const formData = {
                company_name: document.getElementById('companyName').value,
                industry: document.getElementById('industry').value,
                problem: document.getElementById('problem').value,
                solution: document.getElementById('solution').value,
                funding_stage: document.getElementById('fundingStage').value,
                traction: document.getElementById('traction').value
            };
            
            const btn = document.getElementById('generateBtn');
            const output = document.getElementById('outputContent');
            const actionButtons = document.getElementById('actionButtons');
            
            btn.disabled = true;
            btn.textContent = 'Generating...';
            actionButtons.style.display = 'none';
            
            output.innerHTML = '<div class="loading"><div class="spinner"></div><p>Creating your sales pitch...</p></div>';
            
            try {
                const response = await fetch('/api/generate-pitch', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                if (data.error) {
                    output.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${data.error}</p></div>`;
                } else {
                    displayPitch(data);
                    actionButtons.style.display = 'flex';
                }
            } catch (error) {
                output.innerHTML = `<div class="empty-state"><h3>Error</h3><p>Failed to generate pitch. Please try again.</p></div>`;
                console.error('Error:', error);
            }
            
            btn.disabled = false;
            btn.textContent = 'Generate Sales Pitch';
        }
        
        function displayPitch(data) {
            const output = document.getElementById('outputContent');
            
            let html = '<div class="pitch-document">';
            
            // Title
            html += `<h1>${data.company_name || 'Company'} - Investment Opportunity</h1>`;
            
            // Executive Summary
            if (data.executive_summary) {
                html += '<h2>Executive Summary</h2>';
                html += formatContent(data.executive_summary);
            }
            
            // The Opportunity
            if (data.opportunity) {
                html += '<h2>The Opportunity</h2>';
                html += formatContent(data.opportunity);
            }
            
            // Why Us / Why Now
            if (data.why_us) {
                html += '<h2>Why ' + (data.company_name || 'Us') + '</h2>';
                html += formatContent(data.why_us);
            }
            
            // Contact
            if (data.contact) {
                html += '<div class="highlight">';
                html += '<h3>Next Steps</h3>';
                html += formatContent(data.contact);
                html += '</div>';
            }
            
            html += '</div>';
            
            output.innerHTML = html;
        }
        
        function formatContent(text) {
            // Convert line breaks to paragraphs
            let formatted = text.split('\\n\\n').map(para => {
                // Check if it's a bullet point list
                if (para.includes('•') || para.includes('-')) {
                    const items = para.split('\\n').filter(item => item.trim());
                    return '<ul>' + items.map(item => 
                        '<li>' + item.replace(/^[•\-]\s*/, '') + '</li>'
                    ).join('') + '</ul>';
                }
                return '<p>' + para.replace(/\\n/g, ' ') + '</p>';
            }).join('');
            
            return formatted;
        }
        
        function copyPitch() {
            const pitchElement = document.querySelector('.pitch-document');
            if (pitchElement) {
                const text = pitchElement.innerText;
                navigator.clipboard.writeText(text).then(() => {
                    alert('Pitch copied to clipboard!');
                });
            }
        }
        
        function printPitch() {
            window.print();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main application"""
    return Response(HTML_TEMPLATE, mimetype='text/html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_provider": "openai",
        "ai_available": ai_client is not None,
        "model": Config.OPENAI_MODEL if not Config.USE_BUDGET_MODEL else "gpt-3.5-turbo"
    })

@app.route('/api/generate-pitch', methods=['POST'])
def generate_pitch():
    """Generate a 2-3 page sales pitch"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['company_name', 'industry', 'problem', 'solution']
        if not all(data.get(field) for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Select model
        model = "gpt-3.5-turbo" if Config.USE_BUDGET_MODEL else Config.OPENAI_MODEL
        
        # Create the prompt for a clean 2-3 page pitch
        prompt = f"""
        Create a compelling 2-3 page sales pitch for investors. Write in a professional, confident tone.
        
        Company Information:
        - Company Name: {data.get('company_name')}
        - Industry: {data.get('industry')}
        - Funding Stage: {data.get('funding_stage', 'seed')}
        - Current Traction: {data.get('traction', 'Early stage, building momentum')}
        
        Core Value Proposition:
        - Problem: {data.get('problem')}
        - Solution: {data.get('solution')}
        
        Create a pitch with EXACTLY these 3 sections:
        
        1. EXECUTIVE SUMMARY (200-250 words)
        Start with a powerful one-sentence description of what the company does.
        Then cover:
        - The urgent problem we solve and why it matters now
        - Our unique solution and competitive advantage
        - Current traction and momentum
        - The funding we're raising and what we'll achieve with it
        
        2. THE OPPORTUNITY (400-500 words)
        Structure this section with clear sub-points:
        
        The Problem:
        - Expand on the problem with specific pain points
        - Include market inefficiencies and costs to businesses
        - Why existing solutions fall short
        
        Our Solution:
        - How we solve it uniquely
        - Key features and benefits
        - Why our approach is 10x better
        
        Market Opportunity:
        - TAM (Total Addressable Market) in billions
        - Growth rate and market drivers
        - Our serviceable obtainable market
        
        Business Model:
        - How we make money
        - Pricing strategy
        - Unit economics and margins
        
        3. WHY {data.get('company_name').upper()} (250-300 words)
        
        Traction & Validation:
        - Current metrics and growth rate
        - Key customers or partnerships
        - Product-market fit indicators
        
        Our Team:
        - 2-3 key team members with relevant backgrounds
        - Why we're uniquely positioned to win
        
        The Ask:
        - Specific funding amount based on stage
        - 3-4 concrete milestones for next 18 months
        - Vision for the company's future
        
        End with a compelling call to action.
        
        Guidelines:
        - Total length: 850-1050 words (2-3 pages)
        - Use specific numbers and metrics
        - Write in clear, concise paragraphs
        - Avoid bullet points in the main text
        - Be bold but realistic
        - Focus on what makes this investment opportunity exceptional
        
        Return as JSON with keys: executive_summary, opportunity, why_us, contact, company_name
        """
        
        if ai_client:
            try:
                # Make API call to OpenAI
                response = ai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a top-tier venture capital pitch consultant who has helped raise over $1B in funding. Write compelling, concise pitches that get investors excited."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=3000 if not Config.USE_BUDGET_MODEL else 2000,
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                result['company_name'] = data.get('company_name')
                
                # Add contact section if not present
                if 'contact' not in result:
                    result['contact'] = f"Ready to join us in revolutionizing {data.get('industry')}? Let's discuss how {data.get('company_name')} can deliver exceptional returns for your portfolio. Contact our team to schedule a deep dive into our financials, product roadmap, and growth strategy."
                
                logger.info(f"✅ Generated pitch for {data.get('company_name')}")
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"❌ OpenAI API error: {e}")
                return jsonify({"error": "Failed to generate pitch. Please try again."}), 500
        else:
            # Fallback mock response for testing
            logger.info("Using mock response (no API key)")
            
            funding_amounts = {
                "pre-seed": "$500K",
                "seed": "$2M",
                "series-a": "$10M",
                "series-b": "$30M"
            }
            
            funding = funding_amounts.get(data.get('funding_stage', 'seed'), '$2M')
            
            return jsonify({
                "company_name": data.get('company_name'),
                "executive_summary": f"""
{data.get('company_name')} is revolutionizing {data.get('industry')} with an AI-powered platform that {data.get('solution')}. 

The {data.get('industry')} industry faces a critical challenge: {data.get('problem')}. This inefficiency costs businesses millions annually and hampers growth across the sector. Our solution leverages cutting-edge technology to deliver a 10x improvement in efficiency, reducing costs by 60% while improving outcomes.

Since launching six months ago, we've acquired 50+ enterprise customers and are growing at 40% month-over-month. Our current annual recurring revenue has reached $1.2M with a clear path to $10M within 18 months. We're raising {funding} to accelerate product development, expand our sales team, and capture the massive market opportunity ahead of us.
                """.strip(),
                
                "opportunity": f"""
The Problem:
{data.get('problem')} This isn't just an inconvenience—it's a massive drain on resources that affects thousands of companies globally. Current solutions are fragmented, expensive, and fail to address the root cause. Businesses are spending over $50B annually trying to work around these limitations, with most seeing minimal improvement.

Our Solution:
{data.get('company_name')} takes a fundamentally different approach. {data.get('solution')} Our platform integrates seamlessly with existing workflows while providing intelligent automation that learns and improves over time. Key capabilities include real-time analytics, predictive insights, and automated optimization that delivers immediate ROI.

Market Opportunity:
The {data.get('industry')} market represents a $75B total addressable market growing at 25% annually. Digital transformation and AI adoption are accelerating this growth, with enterprises actively seeking solutions like ours. Our serviceable addressable market is $10B, focusing on mid-market and enterprise customers who need sophisticated solutions. We project capturing 1% market share within 5 years, representing a $100M revenue opportunity.

Business Model:
We operate on a SaaS model with three tiers: Starter ($999/month), Professional ($4,999/month), and Enterprise (custom pricing starting at $15,000/month). Our gross margins are 82%, with a customer acquisition cost of $5,000 and lifetime value exceeding $150,000. The model is highly scalable with negative churn due to account expansion.
                """.strip(),
                
                "why_us": f"""
Traction & Validation:
{data.get('traction', 'In just six months, we have achieved remarkable traction')}. Our net revenue retention rate of 140% demonstrates strong product-market fit. We've secured partnerships with three Fortune 500 companies and have a pipeline of 200+ qualified enterprise leads. Customer satisfaction scores average 9.2/10, with several clients reporting 300% ROI within the first quarter.

Our Team:
Our founding team brings deep domain expertise and a track record of success. Our CEO previously scaled a SaaS company from $0 to $50M ARR and successful exit. Our CTO led engineering at two unicorn startups and holds multiple patents in AI/ML. Our VP of Sales built and managed a 100+ person sales organization that generated $200M in annual revenue.

The Ask:
We're raising {funding} to fuel our next phase of growth. This investment will enable us to: (1) Expand our engineering team to accelerate product roadmap, (2) Build out our sales and customer success teams to capture demand, (3) Invest in strategic partnerships and channel development, and (4) Strengthen our market position before competitors emerge.

With this funding, we'll achieve $10M ARR within 18 months and position {data.get('company_name')} as the category leader in {data.get('industry')} innovation.
                """.strip(),
                
                "contact": f"Ready to learn more? Let's discuss how {data.get('company_name')} can deliver exceptional returns for your portfolio. Contact us at invest@{data.get('company_name').lower().replace(' ', '')}.com"
            })
            
    except Exception as e:
        logger.error(f"❌ Error generating pitch: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print(f"""
    {'='*50}
    🚀 AI SALES PITCH GENERATOR
    {'='*50}
    
    Server Configuration:
    - Port: {Config.PORT}
    - Model: {Config.OPENAI_MODEL if not Config.USE_BUDGET_MODEL else 'gpt-3.5-turbo'}
    - AI Status: {'✅ Connected' if ai_client else '❌ No API Key'}
    
    Available Endpoints:
    - GET  /              → Main application UI
    - GET  /health        → Health check
    - POST /api/generate-pitch → Generate 2-3 page pitch
    
    {'='*50}
    Starting server at http://localhost:{Config.PORT}
    {'='*50}
    """)
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=False
    )
