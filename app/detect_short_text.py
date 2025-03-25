import re
import pandas as pd
from typing import List

def detect_and_extract_questions_answers(input_file: str, output_file: str):
    """
    Detects questions that have less than 4 words from an Excel file,
    extracts questions and answers separately, and saves the result in another Excel file.
    """
    # Load the Excel file
    df = pd.read_excel(input_file)
    
    if "content" not in df.columns:
        raise ValueError("The Excel file must contain a 'content' column with question-answer pairs.")
    
    extracted_data = []
    
    for text in df["content"].dropna():
        # Extract question and answer
        match = re.search(r'question:\s*(.*?)\s*answer:\s*(.*)', text, re.DOTALL | re.IGNORECASE)
        
        if match:
            question = match.group(1).strip()
            answer = match.group(2).strip()
            word_count = len(question.split())
            
            if word_count < 5:
                extracted_data.append({"question": question, "answer": answer})
    
    # Save results to an Excel file
    extracted_df = pd.DataFrame(extracted_data)
    extracted_df.to_excel(output_file, index=False)
    print(f"✅ Extracted short questions and answers saved to {output_file}")

# Example usage
detect_and_extract_questions_answers("C:\\Users\\Msi\\Desktop\\Excel_ai_agent\\final cleaned data.xlsx", "short_questions_answers(6words).xlsx")
