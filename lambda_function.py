import json
import boto3
import os
import uuid
import base64

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Set your specific bucket and table names
BUCKET_NAME = 'yogesh-sacred-temple-uploader'
TABLE_NAME = 'sacred-temple-files'
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    # Handle GET request - show upload form
    if event['requestContext']['http']['method'] == 'GET':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
                'Access-Control-Allow-Origin': '*'
            },
            'body': show_upload_form()
        }
    
    # Handle POST request - process file upload
    elif event['requestContext']['http']['method'] == 'POST':
        try:
            # Parse the multipart form data
            content_type = event['headers'].get('content-type', event['headers'].get('Content-Type', ''))
            if 'multipart/form-data' not in content_type:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Invalid content type. Expected multipart/form-data'})
                }
            
            # Parse the body (base64 encoded if isBase64Encoded is true)
            body = event['body']
            if event.get('isBase64Encoded', False):
                body = base64.b64decode(body)
            else:
                body = body.encode('utf-8')
            
            # Parse multipart form data
            boundary = content_type.split("boundary=")[1].encode('utf-8')
            parts = body.split(b'--' + boundary)
            
            file_data = None
            filename = None
            description = None
            
            for part in parts:
                if b'Content-Disposition: form-data;' in part:
                    header_end = part.find(b'\r\n\r\n')
                    if header_end == -1:
                        continue
                    
                    headers = part[:header_end].decode('utf-8')
                    content = part[header_end+4:].rstrip(b'\r\n')
                    
                    if 'name="file"' in headers and 'filename="' in headers:
                        # Extract filename
                        filename_start = headers.find('filename="') + 10
                        filename_end = headers.find('"', filename_start)
                        filename = headers[filename_start:filename_end]
                        file_data = content
                    
                    elif 'name="description"' in headers:
                        description = content.decode('utf-8').strip()
            
            if not filename or not file_data:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'File not found in request'})
                }
            
            # Upload file to S3
            file_id = str(uuid.uuid4())
            file_key = f"uploads/{file_id}_{filename}"
            
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=file_key,
                Body=file_data,
                ContentType='application/octet-stream'
            )
            
            # Generate a presigned URL for the uploaded file
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': file_key},
                ExpiresIn=3600
            )
            
            # Save metadata to DynamoDB
            table.put_item(
                Item={
                    'id': file_id,
                    'filename': filename,
                    'description': description or '',
                    's3_key': file_key,
                    'upload_date': str(context.aws_request_id),
                    'presigned_url': presigned_url
                }
            )
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/html',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': show_success_message(filename, file_id, presigned_url)
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': str(e)})
            }
    
    # Handle other methods
    else:
        return {
            'statusCode': 405,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }

def show_upload_form():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sacred Temple Upload | Majisimpleb</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Poppins:wght@300;400;500&display=swap');
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
                background-size: 400% 400%;
                animation: gradientShift 15s ease infinite;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                overflow-x: hidden;
                color: #fff;
            }
            
            @keyframes gradientShift {
                0% { background-position: 0% 50% }
                50% { background-position: 100% 50% }
                100% { background-position: 0% 50% }
            }
            
            .container {
                width: 90%;
                max-width: 600px;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.2);
                position: relative;
                z-index: 2;
            }
            
            .temple-roof {
                position: absolute;
                top: -50px;
                left: 50%;
                transform: translateX(-50%);
                width: 200px;
                height: 100px;
                background: linear-gradient(45deg, #8B4513, #A0522D);
                clip-path: polygon(0% 100%, 50% 0%, 100% 100%);
                z-index: 1;
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
            }
            
            .temple-roof::before {
                content: '';
                position: absolute;
                top: 10px;
                left: 10px;
                right: 10px;
                height: 20px;
                background: linear-gradient(45deg, #CD853F, #D2691E);
                clip-path: polygon(0% 100%, 50% 0%, 100% 100%);
            }
            
            .temple-pillars {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                display: flex;
                justify-content: space-around;
                height: 100px;
            }
            
            .pillar {
                width: 20px;
                height: 100%;
                background: linear-gradient(to bottom, #8B4513, #A0522D, #8B4513);
                border-radius: 5px 5px 0 0;
                position: relative;
            }
            
            .pillar::before {
                content: '';
                position: absolute;
                top: 10px;
                left: -5px;
                right: -5px;
                height: 15px;
                background: #D2691E;
                border-radius: 3px;
            }
            
            .floating-element {
                position: absolute;
                opacity: 0.7;
                z-index: 1;
            }
            
            .floating-1 {
                top: 10%;
                left: 5%;
                width: 30px;
                height: 30px;
                background: radial-gradient(circle, #ffd700, transparent);
                border-radius: 50%;
                animation: float 6s ease-in-out infinite;
            }
            
            .floating-2 {
                top: 20%;
                right: 10%;
                width: 40px;
                height: 40px;
                background: radial-gradient(circle, #ff6b6b, transparent);
                border-radius: 50%;
                animation: float 8s ease-in-out infinite 1s;
            }
            
            .floating-3 {
                bottom: 30%;
                left: 15%;
                width: 25px;
                height: 25px;
                background: radial-gradient(circle, #4ecdc4, transparent);
                border-radius: 50%;
                animation: float 7s ease-in-out infinite 2s;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0) rotate(0deg); }
                50% { transform: translateY(-20px) rotate(180deg); }
            }
            
            h1 {
                font-family: 'Playfair Display', serif;
                text-align: center;
                margin: 20px 0 10px;
                font-size: 2.5rem;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
                background: linear-gradient(to right, #ffd700, #ff6b6b, #4ecdc4);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .subtitle {
                text-align: center;
                margin-bottom: 30px;
                font-size: 1.1rem;
                opacity: 0.9;
            }
            
            .form-group {
                margin-bottom: 25px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
            }
            
            input[type="text"], input[type="file"] {
                width: 100%;
                padding: 15px;
                border: none;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                transition: all 0.3s ease;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            }
            
            input[type="text"]:focus, input[type="file"]:focus {
                outline: none;
                background: rgba(255, 255, 255, 1);
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
            }
            
            .upload-btn {
                width: 100%;
                padding: 15px;
                background: linear-gradient(45deg, #ff6b6b, #ffd700);
                border: none;
                border-radius: 10px;
                color: #fff;
                font-size: 18px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                position: relative;
                overflow: hidden;
            }
            
            .upload-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            }
            
            .upload-btn:active {
                transform: translateY(1px);
            }
            
            .upload-btn::after {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                transition: left 0.5s;
            }
            
            .upload-btn:hover::after {
                left: 100%;
            }
            
            .instructions {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 20px;
                margin-top: 30px;
                border-left: 4px solid #ffd700;
            }
            
            .instructions h3 {
                margin-bottom: 10px;
                color: #ffd700;
            }
            
            .instructions ul {
                padding-left: 20px;
            }
            
            .instructions li {
                margin-bottom: 8px;
                line-height: 1.4;
            }
            
            .diya {
                position: absolute;
                bottom: -30px;
                left: 50%;
                transform: translateX(-50%);
                width: 60px;
                height: 60px;
                background: radial-gradient(ellipse at center, #ffd700 0%, #ff6b00 70%);
                border-radius: 50%;
                filter: blur(5px);
                animation: flicker 3s infinite alternate;
                z-index: 0;
            }
            
            @keyframes flicker {
                0%, 100% { opacity: 0.8; transform: translateX(-50%) scale(1); }
                50% { opacity: 1; transform: translateX(-50%) scale(1.1); }
            }
            
            @media (max-width: 768px) {
                .container {
                    width: 95%;
                    padding: 20px;
                }
                
                h1 {
                    font-size: 2rem;
                }
                
                .temple-roof {
                    width: 150px;
                    height: 75px;
                    top: -40px;
                }
            }
        </style>
    </head>
    <body>
        <div class="floating-element floating-1"></div>
        <div class="floating-element floating-2"></div>
        <div class="floating-element floating-3"></div>
        
        <div class="temple-roof"></div>
        <div class="temple-pillars">
            <div class="pillar"></div>
            <div class="pillar"></div>
            <div class="pillar"></div>
            <div class="pillar"></div>
            <div class="pillar"></div>
        </div>
        
        <div class="container">
            <h1>Sacred Temple Upload</h1>
            <p class="subtitle">Offer your files to the digital temple of yogesh-sacred-temple-uploader</p>
            
            <form method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="description">Blessing Message (Description):</label>
                    <input type="text" id="description" name="description" placeholder="Enter a blessing for your file">
                </div>
                <div class="form-group">
                    <label for="file">Select your sacred offering (File):</label>
                    <input type="file" id="file" name="file" required>
                </div>
                <button type="submit" class="upload-btn">Offer to the Temple</button>
            </form>
            
            <div class="instructions">
                <h3>How the Temple Blesses Your Files:</h3>
                <ul>
                    <li>Your offerings are stored in the sacred S3 bucket: yogesh-sacred-temple-uploader</li>
                    <li>File blessings (metadata) are recorded in the temple scrolls (DynamoDB)</li>
                    <li>You'll receive a temporary sacred link to retrieve your offering</li>
                    <li>The sacred link expires after 1 hour to maintain temple sanctity</li>
                </ul>
            </div>
        </div>
        
        <div class="diya"></div>
        
        <script>
            // Add some interactive animations
            document.addEventListener('DOMContentLoaded', function() {
                const inputs = document.querySelectorAll('input');
                
                inputs.forEach(input => {
                    input.addEventListener('focus', function() {
                        this.parentElement.style.transform = 'translateY(-5px)';
                    });
                    
                    input.addEventListener('blur', function() {
                        this.parentElement.style.transform = 'translateY(0)';
                    });
                });
                
                // Add floating animation to container using Date instead of Math
                const container = document.querySelector('.container');
                function updateFloat() {
                    const time = new Date().getTime() / 1000;
                    const floatValue = time % 2 > 1 ? 3 - (time % 2) * 2 : (time % 2) * 2;
                    container.style.transform = 'translateY(' + floatValue + 'px)';
                    requestAnimationFrame(updateFloat);
                }
                updateFloat();
            });
        </script>
    </body>
    </html>
    """

def show_success_message(filename, file_id, presigned_url):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Offering Accepted | Sacred Temple Upload</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Poppins:wght@300;400;500&display=swap');
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
                background-size: 400% 400%;
                animation: gradientShift 15s ease infinite;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                overflow-x: hidden;
                color: #fff;
            }}
            
            @keyframes gradientShift {{
                0% {{ background-position: 0% 50% }}
                50% {{ background-position: 100% 50% }}
                100% {{ background-position: 0% 50% }}
            }}
            
            .container {{
                width: 90%;
                max-width: 700px;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.2);
                text-align: center;
                position: relative;
                z-index: 2;
            }}
            
            .success-icon {{
                font-size: 80px;
                color: #4CAF50;
                margin-bottom: 20px;
                text-shadow: 0 0 20px rgba(76, 175, 80, 0.7);
                animation: pulse 2s infinite;
            }}
            
            @keyframes pulse {{
                0% {{ transform: scale(1); }}
                50% {{ transform: scale(1.1); }}
                100% {{ transform: scale(1); }}
            }}
            
            h1 {{
                font-family: 'Playfair Display', serif;
                margin-bottom: 10px;
                font-size: 2.5rem;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
                background: linear-gradient(to right, #4CAF50, #8BC34A, #CDDC39);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            
            .subtitle {{
                margin-bottom: 30px;
                font-size: 1.2rem;
                opacity: 0.9;
            }}
            
            .offering-details {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 25px;
                margin: 25px 0;
                text-align: left;
                border-left: 4px solid #4CAF50;
            }}
            
            .offering-details p {{
                margin-bottom: 15px;
                font-size: 1.1rem;
            }}
            
            .offering-details strong {{
                color: #ffd700;
            }}
            
            .action-buttons {{
                display: flex;
                flex-direction: column;
                gap: 15px;
                margin: 30px 0;
            }}
            
            .btn {{
                padding: 15px 30px;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            }}
            
            .btn-primary {{
                background: linear-gradient(45deg, #4CAF50, #8BC34A);
                color: white;
            }}
            
            .btn-secondary {{
                background: rgba(255, 255, 255, 0.2);
                color: white;
            }}
            
            .btn:hover {{
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            }}
            
            .note {{
                background: rgba(255, 193, 7, 0.2);
                border-radius: 10px;
                padding: 15px;
                margin-top: 20px;
                border-left: 4px solid #ffc107;
            }}
            
            .floating-element {{
                position: absolute;
                opacity: 0.7;
                z-index: 1;
            }}
            
            .floating-1 {{
                top: 10%;
                left: 5%;
                width: 30px;
                height: 30px;
                background: radial-gradient(circle, #4CAF50, transparent);
                border-radius: 50%;
                animation: float 6s ease-in-out infinite;
            }}
            
            .floating-2 {{
                top: 20%;
                right: 10%;
                width: 40px;
                height: 40px;
                background: radial-gradient(circle, #8BC34A, transparent);
                border-radius: 50%;
                animation: float 8s ease-in-out infinite 1s;
            }}
            
            .floating-3 {{
                bottom: 30%;
                left: 15%;
                width: 25px;
                height: 25px;
                background: radial-gradient(circle, #CDDC39, transparent);
                border-radius: 50%;
                animation: float 7s ease-in-out infinite 2s;
            }}
            
            @keyframes float {{
                0%, 100% {{ transform: translateY(0) rotate(0deg); }}
                50% {{ transform: translateY(-20px) rotate(180deg); }}
            }}
            
            .temple-gate {{
                position: absolute;
                bottom: -50px;
                left: 50%;
                transform: translateX(-50%);
                width: 200px;
                height: 100px;
                background: linear-gradient(45deg, #5D4037, #6D4C41);
                clip-path: polygon(0% 100%, 30% 0%, 70% 0%, 100% 100%);
                z-index: 1;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    width: 95%;
                    padding: 20px;
                }}
                
                h1 {{
                    font-size: 2rem;
                }}
                
                .action-buttons {{
                    flex-direction: column;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="floating-element floating-1"></div>
        <div class="floating-element floating-2"></div>
        <div class="floating-element floating-3"></div>
        
        <div class="container">
            <div class="success-icon">✓</div>
            <h1>Offering Accepted!</h1>
            <p class="subtitle">The temple has blessed your file</p>
            
            <div class="offering-details">
                <p><strong>Sacred Name:</strong> {filename}</p>
                <p><strong>Offering ID:</strong> {file_id}</p>
                <p><strong>Temple Blessing Link:</strong> <a href="{presigned_url}" style="color: #4CAF50; word-break: break-all;">Click to receive blessing</a></p>
            </div>
            
            <div class="action-buttons">
                <a href="{presigned_url}" class="btn btn-primary" target="_blank">Receive Blessing (Download)</a>
                <a href="/" class="btn btn-secondary">Make Another Offering</a>
            </div>
            
            <div class="note">
                <strong>Note from the Temple Priests:</strong> This sacred link will expire after 1 hour to maintain the temple's spiritual balance.
                For eternal access, consult with the high priests of AWS.
            </div>
        </div>
        
        <div class="temple-gate"></div>
        
        <script>
            // Add celebration animation
            document.addEventListener('DOMContentLoaded', function() {{
                const container = document.querySelector('.container');
                
                // Floating animation using Date instead of Math
                function updateFloat() {{
                    const time = new Date().getTime() / 1000;
                    const floatValue = time % 2 > 1 ? 5 - (time % 2) * 5 : (time % 2) * 5;
                    container.style.transform = 'translateY(' + floatValue + 'px)';
                    requestAnimationFrame(updateFloat);
                }}
                updateFloat();
                
                // Add floating particles on load
                for (let i = 0; i < 20; i++) {{
                    createParticle();
                }}
                
                function createParticle() {{
                    const particle = document.createElement('div');
                    particle.style.position = 'fixed';
                    particle.style.width = '5px';
                    particle.style.height = '5px';
                    particle.style.background = '#4CAF50';
                    particle.style.borderRadius = '50%';
                    particle.style.left = (i * 5) + '%';
                    particle.style.top = '100vh';
                    particle.style.opacity = '0.7';
                    particle.style.zIndex = '1';
                    document.body.appendChild(particle);
                    
                    // Animate particle using simple calculations
                    const duration = 2000 + (i % 10) * 1000;
                    const targetY = - (50 + (i % 5) * 20);
                    
                    const startTime = Date.now();
                    
                    function animateParticle() {{
                        const currentTime = Date.now();
                        const elapsed = currentTime - startTime;
                        const progress = elapsed / duration;
                        
                        if (progress < 1) {{
                            particle.style.transform = 'translateY(' + (targetY * progress) + 'vh) scale(' + (1 - progress) + ')';
                            particle.style.opacity = 0.7 * (1 - progress);
                            requestAnimationFrame(animateParticle);
                        }} else {{
                            particle.remove();
                            createParticle();
                        }}
                    }}
                    
                    animateParticle();
                }}
            }});
        </script>
    </body>
    </html>
    """

# For local testing
if __name__ == "__main__":
    # Mock event for testing
    test_event = {
        'requestContext': {
            'http': {
                'method': 'GET'
            }
        },
        'headers': {}
    }
    
    # Test the function
    result = lambda_handler(test_event, None)
    print("Status Code:", result['statusCode'])
    print("Headers:", result['headers'])
    print("Body length:", len(result['body']))
