import time
import fitz
import base64
import json
import openai
from openai import OpenAI
from pydantic import BaseModel, Field
from config import Config

openai.api_key = Config.OPENAI_API_KEY
client = OpenAI(api_key=Config.OPENAI_API_KEY)

# model for the ai output
class UtilityBill(BaseModel):
    service_name: str = Field(description="The generic utility category. Use standard types: 'Electric', 'Gas', 'Water', 'Internet', 'Trash', or 'Sewer'. NEVER include company names like PG&E or Spectrum.")
    service_period: str = Field(description="The billing cycle dates formatted strictly as 'MM-DD-YYYY to MM-DD-YYYY'.")
    billing_start_month: str = Field(description="The month and year the service started, derived from the raw_service_period. Format: 'Month YYYY'. If the start date is the very end of a month (e.g., 30th/31st), use the next month. (e.g., '10-31-2025' to '12-02-2025' is 'November 2025').")
    total_amount_due: float = Field(description="The final total amount due on the bill. Use 0.0 if not found.")

# extracts the text from the pdf
def extract_from_pdf(uploaded_file):
    uploaded_file.seek(0)
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    extracted_text = ""
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        extracted_text += f"\n---PAGE {page_num + 1} ---\n"
        extracted_text += page.get_text("text").strip()

    return extracted_text
    
# sends text to ai and extracts billing information
def get_bill_details(extracted_text):
    prompt = """
    You are an expert data extraction AI. Extract billing details from the provided text using these logic rules.
    
    1. CATEGORY MAPPING (MANDATORY):
       - Ignore all company branding and legal names.
       - Map the bill to one of these specific categories: 'Electric', 'Gas', 'Water', 'Internet', 'Trash', 'Sewer'.
       - If a bill contains multiple services (e.g., Water and Sewer), use a combined label like 'Water and Sewer'.
       - Example: 'Pacific Gas and Electric' -> 'Electric'.
       - Example: 'Spectrum' or 'Xfinity' -> 'Internet'.
       - Example: 'City of San Luis Obispo - Water and Sewer' -> 'Water and Sewer'.

    2. SMART MONTH LOGIC:
       - The 'billing_start_month' should represent the primary month of service.
       - If the service starts on the 30th of the month or later, assign the bill to the FOLLOWING month.
       - Example: '10-31-2025 to 12-02-2025' should be 'November 2025'.
       - Example: '09-28-2025 to 10-27-2025' should be 'September 2025'.

    3. DATA INTEGRITY:
       - Format 'service_period' strictly as 'MM-DD-YYYY to MM-DD-YYYY' (e.g., '09-24-2025 to 10-23-2025').
       - If a service period lacks a year (e.g., 'Sep 24 - Oct 23'), look at the Statement Date, Issue Date, or Due Date elsewhere in the text to logically infer the correct year. NEVER use 'valued customer since' dates.
       - Extract the final total amount due.
       - If the text does not look like a utility bill, return 'Unknown' for strings and 0.0 for amounts.
    """
    
    max_retries = 4
    for attempt in range(max_retries):
        try:
            completion = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": extracted_text}
                ],
                response_format=UtilityBill,
            )
            
            result = completion.choices[0].message.parsed
            
            return{
                "Billing Month": result.billing_start_month,
                "Service Name": result.service_name,
                "Service Period": result.service_period,
                "Total Amount Due": result.total_amount_due
            }
        except Exception as e:
            wait_time = 5 * (2 ** attempt)
            print(f"Error occurred: {e}. Sleeping for {wait_time}s. Attempt: {attempt + 1}")
            time.sleep(wait_time)
            
    print(f"All attempts failed")
    return {
        "Billing Month": "Error",
        "Service Name": "Error", 
        "Service Period": "Error", 
        "Total Amount Due": 0.0
    }
    
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

def extract_from_receipt_image(image_file):
    image_file.seek(0)
    base64_image = encode_image(image_file)
    prompt = """
    You are an AI receipt parser. Analyze this receipt image and extract all purchased items and their exact prices.
    Ignore tax, tip, and the grand total. 
    
    You must respond in strict JSON format. 
    Return an object with a single key "items", which contains an array of objects.
    Each object must have exactly two keys:
    1. "Service Name" (string: the name of the item)
    2. "Total Amount Due" (float: the price of the item)
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={ "type": "json_object" },
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
        )
        
        response_json = json.loads(response.choices[0].message.content)
        items_list = response_json.get("items", [])
        
        for item in items_list:
            item["Billing Month"] = "Pending" 
            item["Service Period"] = "One-Time Charge"
            
        return items_list
    except Exception as e:
        print(f"Error processing receipt image: {e}")
        raise e