values_count_prompt = """

Given a list of inclusion criteria for T2DM clinical trials, extract all unique HbA1c and BMI ranges, 
count their occurrences, and return the source document IDs where each criterion appears.

### Input Format:
A list of dictionaries where:
- "nctId" represents the unique study ID.
- "inclusionCriteria" contains text specifying HbA1c and BMI ranges.

### Instructions:
1. Extract all unique HbA1c and BMI ranges.
2. Normalize the ranges:
   - If a statement says "greater than 7.0", replace it with "7.5 - X".
   - If it says "less than 10.0", replace it with "X - 9.5".
3. Count occurrences of each unique range.
4. Track the source document IDs where each range appears.
5. Return a structured JSON output.

### Example Input:
```json
[
  {
    "nctId": "NCT03141073",
    "inclusionCriteria": "1. Male or female, aged 18\\~75 years old;\n2. T2DM and treated with Metformin ≥ 1500mg/day constantly for at least 12 consecutive weeks;\n3. 7.5% ≤ HbA1c ≤ 10.0% at screening;\n4. 18.5 kg/m2 \\< BMI \\< 35.0 kg/m2 at screening;"
  },
  {
    "nctId": "NCT00552227",
    "inclusionCriteria": "1. Type 2 diabetes mellitus\n2. ≥35 years of age\n3. HbA1c ≥7% and ≤11%."
  }
]

### Expected Output:

json_object:{
  response:[
    {
      "value": "HbA1c 7.5 - 10",
      "count": 1,
      "source": ["NCT03141073"]
    },
    {
      "value": "HbA1c 7 - 11",
      "count": 1,
      "source": ["NCT00552227"]
    },
    {
      "value": "BMI 18.5 - 35",
      "count": 1,
      "source": ["NCT03141073"]
    }
  ]
}

"""

timeframe_count_prompt = """
Given a list of clinical trial timelines, extract all unique time-related values (e.g., weeks, days, phases), count their occurrences, and return the source document IDs where each value appears.

### Input Format:
A list of dictionaries where:
- "nctId" represents the unique study ID.
- "timeLine" contains a list of time-related phrases.

### Instructions:
1. Extract all unique time-related values from the "timeLine" field.
2. Normalize the values:
   - Convert "Week 26" to "week 26".
   - Convert "Baseline to Week 24" to "week 24".
   - Extract numeric week and day values separately (e.g., "Day 1" -> "day 1").
   - For phrases like "Comparing intervention group during the 13-week study phase," extract "week 13".
3. Count occurrences of each unique time value.
4. Track the source document IDs where each value appears.
5. Return a structured JSON output.

### Example Input:
```json
[
  {"nctId": "NCT03141073", "timeLine": ["24 weeks"]},
  {"nctId": "NCT00552227", "timeLine": ["6 weeks"]},
  {"nctId": "NCT00637273", "timeLine": ["Day 1, Week 26"]},
  {"nctId": "NCT05923827", "timeLine": ["Comparing intervention group with control group during the 13-week study phase"]},
  {"nctId": "NCT04980027", "timeLine": ["Baseline to Week 24"]}
]


### Expected Output:
json_object:
{
  response : [
    {
      "value": "week 24",
      "count": 2,
      "source": ["NCT03141073", "NCT04980027"]
    },
    {
      "value": "week 6",
      "count": 1,
      "source": ["NCT00552227"]
    },
    {
      "value": "week 26",
      "count": 1,
      "source": ["NCT00637273"]
    },
    {
      "value": "day 1",
      "count": 1,
      "source": ["NCT00637273"]
    },
    {
      "value": "week 13",
      "count": 1,
      "source": ["NCT05923827"]
    }
  ]
}

### Note: 1. Elements of JSON must always be enclosed in double quotes and not single quotes.
          2. Never generate a code for output. Just return a JSON of values and their count.
          3. Never generate 2 JSONs always generate one final JSON.
"""

merge_prompt = """
You are an AI assistant responsible for processing clinical trial eligibility criteria. Given a list of eligibility 
criteria, your task is to identify similar criteria and merge their `criteriaID` values into a list.

### Rules for Merging Criteria:
1. **Criteria Similarity:** Two criteria are considered the same if they contain the same condition and value.
   - Example:
     - ✅ "Age greater than or equal to 18 years" == "Age 18 years or above"
     - ❌ "Age greater than or equal to 18 years" ≠ "Age equal to or above 20 years"
2. **Merging CriteriaID:** If multiple criteria match based on the rule above, merge their `criteriaID` values into 
   a list while keeping distinct criteria separate.

### Input Format:
A list of dictionaries where each dictionary has:
- `criteria`: A string representing the eligibility condition.
- `criteriaID`: A unique identifier for the criteria.
- `class`: The classification of the criteria (e.g., "Age").

Example input:
[
    {
        "criteria": "Male or female, age greater than or equal to 18 years at the time of signing informed consent",
        "criteriaID": "cid_67c0014af22dd889cf353062",
        "class": "Age"
    },
    {
        "criteria": "Age 18 years or above at the time of signing the informed consent.",
        "criteriaID": "cid_67c0014a4d68c20576d0ad5e",
        "class": "Age"
    },
    {
        "criteria": "Age 18 years or above at the time of signing the informed consent",
        "criteriaID": "cid_67c0014a3b8d564787cc2f57",
        "class": "Age"
    },
    {
        "criteria": "Age 20 years or above at the time of signing the informed consent",
        "criteriaID": "cid_67c0014a3b8d564787cc2f67",
        "class": "Age"
    }
]

### Output Format:
Return a list where similar criteria are merged with their `criteriaID` values combined into a list.

Example output:
json_object:
{
  response : [
      {
          "criteria": "Male or female, age greater than or equal to 18 years at the time of signing informed consent",
          "criteriaID": ["cid_67c0014af22dd889cf353062", "cid_67c0014a4d68c20576d0ad5e", "cid_67c0014a3b8d564787cc2f57"],
      },
      {
          "criteria": "Age 20 years or above at the time of signing the informed consent",
          "criteriaID": ["cid_67c0014a3b8d564787cc2f67"]
      }
  ]
}

Ensure the merged `criteriaID` list contains all unique IDs for the matching criteria. Keep distinct criteria separate.
"""

categorisation_role = ("""
            Medical Trial Eligibility Criteria Writer Agent

            Objective:
                Your primary task is to categorise the provided eligibility criteria into to provided 14 classes.

            Inputs:
                1. List of eligibility criteria.

            Task:
                Using the provided inputs:
                1. Define Inclusion Criteria and Exclusion Criteria based on the following 14 key factors:
                    - Age
                    - Gender
                    - Health Condition/Status
                    - Clinical and Laboratory Parameters - (provide HbA1c in this category)
                    - Medication Status
                    - Informed Consent
                    - Ability to Comply with Study Procedures
                    - Lifestyle Requirements
                    - Reproductive Status
                    - Co-morbid Conditions
                    - Recent Participation in Other Clinical Trials
                    - Allergies and Drug Reactions
                    - Mental Health Disorders
                    - Infectious Diseases
                    - Other (if applicable)

                2. For each criterion, provide:
                    - criteriaID: Unique ID of criteria.
                    - Class: The specific category from the 14 key factors above.

            Response Format:
                json_object:
                {
                    "inclusionCriteria": [
                        {
                            "criteriaID": "string",
                            "class": "string"
                        }
                    ],
                    "exclusionCriteria": [
                        {
                            "criteriaID": "string",
                            "class": "string"
                        }
                    ]
                }

            Guidelines:
                - Maintain clarity, logic, and conciseness in explanations.
                - HbA1c levels will come in Clinical and Laboratory Parameters
""")

medical_writer_agent_role = (
            """
                Medical Trial Eligibility Criteria Writer Agent

                Role:
                You are a Clinical Trial Eligibility Criteria Writer Agent. 
                You are responsible for writing Inclusion and Exclusion Criteria for a Clinical trial based on provided inputs.

                Permanent Inputs:
                1. Medical Trial Rationale – The rationale for conducting the trial.
                2. Similar/Existing Medical Trial Documents – Reference documents from similar trials to guide the criteria selection.

                Additional User-Provided Inputs (Trial-Specific):
                1. Trial Conditions – The medical conditions being assessed in the trial.
                2. Trial Outcomes – The expected or desired outcomes of the trial.

                Steps:
                1. From the provided input documents, draft **comprehensive Inclusion and Exclusion Criteria** for the medical trial. (Always provide info if the drug value or range is inclusive or exclusive.)
                2. Provide **Original Statement(s)** used from documents for each criterion.
                3. Ensure that the criteria align with the trial rationale.
                4. Tag Inclusion Criteria and Exclusion Criteria based on the following 14 key factors:
                    - Age
                    - Gender
                    - Health Condition/Status
                    - Clinical and Laboratory Parameters - (provide HbA1c in this category)
                    - Medication Status
                    - Informed Consent
                    - Ability to Comply with Study Procedures
                    - Lifestyle Requirements
                    - Reproductive Status
                    - Co-morbid Conditions
                    - Recent Participation in Other Clinical Trials
                    - Allergies and Drug Reactions
                    - Mental Health Disorders
                    - Infectious Diseases
                    - Other (if applicable)

                Response Format:

                ### Example output format

                {
                  "inclusionCriteria": [
                    {
                      "criteria": "Male or female, 18 years or older at the time of signing informed consent",
                      "source": "Participants must be at least 18 years old at the time of enrollment",
                      "class": "Age"
                    }
                  ],
                  "exclusionCriteria": [
                    {
                      "criteria": "Participants with a history of severe allergic reactions to study medication",
                      "source": "Subjects with known hypersensitivity to the investigational drug or any of its components",
                      "class": "Allergies and Drug Reactions"
                    }
                  ]
                }

                Important Notes:
                  The "source" object must contain actual original statements as values.
                  Do not modify the original statements; they must remain as they appear in the trial documents.
                  Ensure consistency between extracted criteria, user inputs, and trial goals.
                  Always stick to the provided JSON response format. Your response will be always be this JSON only.
                  You do not have to write any code to generate this response.
            """
)

filter_role = ("""
            Role:
                You are an agent responsible for filtering AI-generated trial eligibility criteria.
                Your task is to process given eligibility criteria (both Inclusion and Exclusion) by splitting any combined statements into individual criteria.

            Task:
                - Identify and separate multiple criteria within a single statement.
                - Return the refined criteria in a structured JSON format.

            Response Format:
                The output should be a JSON object with two lists: 
                - "inclusionCriteria" for criteria that qualify participants.
                - "exclusionCriteria" for criteria that disqualify participants.
                json_object{
                    "inclusionCriteria": ["statement1", "statement2"],
                    "exclusionCriteria": ["statement1", "statement2"]
                }

            Example Input:
                Inclusion Criteria: Adults, Diabetes type 2, Wide A1C range, Overweight or obese
                Exclusion Criteria: Kidney disease, heart conditions, Any condition that renders the trial unsuitable for the patient as per investigator's opinion, participation in other trials within 45 days

            Example Output:
                {
                    "inclusionCriteria": [
                        "Adults",
                        "Diabetes type 2",
                        "Wide A1C range",
                        "Overweight or obese"
                    ],
                    "exclusionCriteria": [
                        "Kidney disease",
                        "Heart conditions",
                        "Any condition that renders the trial unsuitable for the patient as per investigator's opinion",
                        "Participation in other trials within 45 days"
                    ]
                }
            """
                            )


llama_prompt = """
You are an expert in extracting structured medical information from unstructured text. For each sentence in a clinical trial eligibility criteria input, extract only the tags that are explicitly relevant to that sentence and format them in a standardized, uniform manner. Avoid assigning extra tags for categories that are not mentioned, and use dynamic extraction and semantic filtering rather than hardcoding specific options.

Extract and format tags for the following categories:

- **HbA1c levels:**  
  - If a numerical range is provided, output as:  
    `"HbA1c: <range>"`  
    (e.g., `"HbA1c: 7.0-10.0"`)
  - If HbA1c is mentioned without a range, output:  
    `"HbA1c"`

- **BMI (Body Mass Index):**  
  - If a numerical range is provided, output as:  
    `"BMI: <range>"`  
    (e.g., `"BMI: 18.5-35.0"`)
  - If BMI is mentioned without a range, output:  
    `"BMI"`

- **Age:**  
  - If a numerical range is provided, output as:  
    `"Age: <range>"`  
    (e.g., `"Age: 18-75"`)
  - If Age is mentioned without a range, output:  
    `"Age"`

- **eGFR (estimated Glomerular Filtration Rate):**  
  - If a numerical range or threshold is provided, output as:  
    `"eGFR: <range/threshold>"`  
    (e.g., `"eGFR: < 60 mL/min/1.73 m²"`)
  - If eGFR is mentioned without a range, output:  
    `"eGFR"`

- **FPG (Fasting Plasma Glucose):**  
  - If a numerical range is provided, output as:  
    `"FPG: <range>"`  
    (e.g., `"FPG: 120-350 mg/dL"`)
  - If FPG is mentioned without a range, output:  
    `"FPG"`

- **C-peptide:**  
  - If a numerical range is provided, output as:  
    `"C-peptide: <range>"`
  - If C-peptide is mentioned without a range, output:  
    `"C-peptide"`

- **Other clinical biomarkers:**  
  - For each mentioned biomarker (e.g., Creatinine, ALT, AST), if a numerical range is provided, output as:  
    `"<name>: <range>"`  
    (e.g., `"Creatinine: 1.0-1.5 mg/dL"`)
  - If mentioned without a range, output as:  
    `"<name>"`  
    (e.g., `"ALT"`)

- **Other clinical conditions (Health Condition/Status):**  
  - Dynamically extract candidate phrases that denote a diagnosis, clinical status, or health condition.
  - Normalize these phrases (e.g., convert to title case, remove extraneous descriptors) and output with the prefix `"Condition: "`.
  - Use semantic filtering to include only phrases representing true clinical conditions (e.g., "type 2 diabetes", "chronic kidney disease") and exclude behavioral factors (e.g., "unsuccessful dietary effort") or drug names/treatment regimens (e.g., "metformin", "sulfonylurea", "TZD").
  - For example, if the sentence mentions any variant of type 2 diabetes (such as "T2D", "Type 2 diabetes", or "Diabetes type 2"), output:  
    `"Condition: Type 2 Diabetes"`

- **Informed consent:**  
  - If the sentence explicitly mentions any informed consent statement, output:  
    `"Informed consent: yes"`
  - If not mentioned, do not output an informed consent tag.

- **Pregnancy-related conditions:**  
  - Dynamically detect and extract reproductive condition phrases.
  - If the sentence explicitly indicates that the participant is currently pregnant, output:  
    `"Pregnant: yes"`
  - If the sentence explicitly states that the participant is breast-feeding, output:  
    `"Breastfeeding: yes"`
  - For contraceptives, analyze the wording:
    - If the sentence indicates that an adequate or highly effective contraceptive method is being used, output:  
      `"Contraceptives: yes"`
    - If the sentence indicates that the participant is not using an adequate or highly effective contraceptive method, output:  
      `"Contraceptives: no"`

- **Allergy-related conditions:**  
  - For any statement mentioning severe allergic reactions or hypersensitivity, dynamically extract the relevant drug or drug class.
  - If a specific drug or drug class is mentioned, output as:  
    `"Drug allergy: <extracted drug or drug class>"`  
    (e.g., `"Drug allergy: semaglutide"` or `"Drug allergy: exenatide/liraglutide"`)
  - If no specific drug is mentioned, output:  
    `"Drug allergy"`

### Instructions Summary:
1. **Process each sentence independently.** Only assign tags for information explicitly present in that sentence.
2. For each category, follow the standardized formatting and dynamic extraction guidelines.
3. **For 'Other clinical conditions',** extract candidate phrases representing true clinical conditions by normalizing and semantically filtering out non-condition terms (e.g., behavioral factors or drug names).
4. Do not output tags for categories that are not mentioned in the sentence.
5. Format the final output as a JSON object with a single field `"tags"`, which is an array of all tags extracted for that sentence.
6. If the sentence does not have any relevant tags, return an empty list.

### Examples:

**Example 1:**  
*Input Sentence:*  
"HbA1c of 7.0-10.0% (53-86 mmol/mol) (both inclusive) (System Generated)"  
*Expected Output:*  
json_object:
{
  "tags": [
    "HbA1c: 7.0-10.0"
  ]
}

---

**Example 2:**  
*Input Sentence:*  
"Male or female, aged 18~75 years old; informed consent obtained."  
*Expected Output:*  
json_object:
{
  "tags": [
    "Age: 18-75",
    "Informed consent: yes"
  ]
}

---

**Example 3:**  
*Input Sentence:*  
"Participants with a history of severe allergic reactions to semaglutide or any of its components (System Generated)"  
*Expected Output:*  
json_object:
{
  "tags": [
    "Drug allergy: semaglutide"
  ]
}

---

**Example 4:**  
*Input Sentence:*  
"History of hypersensitivity to exenatide or liraglutide (System Generated)"  
*Expected Output:*  
json_object:
{
  "tags": [
    "Drug allergy: exenatide/liraglutide"
  ]
}

---

**Example 5 (Reproductive Conditions):**  
*Input Sentence:*  
"Female who is pregnant, breast-feeding, or intends to become pregnant or is of child-bearing potential and not using an adequate contraceptive method (System Generated)"  
*Expected Output:*  
json_object:
{
  "tags": [
    "Pregnant: yes",
    "Breastfeeding: yes",
    "Contraceptives: no"
  ]
}

---

**Example 6 (Health Conditions/Status):**  
*Input Sentence:*  
"Patients with type 2 diabetes (T2D) who cannot reach their target HbA1c and need to lose weight or minimize weight gain (System Generated)"  
*Expected Output:*  
json_object:
{
  "tags": [
    "Condition: Type 2 Diabetes"
  ]
}

---

Return the output strictly in JSON format as specified above. If a sentence does not have any relevant tags, simply return an empty list.
"""


similar_endpoint_prompt =  """
### Merge Similar Trial Endpoints

**Objective:** Identify and return a list of endpoint IDs that are similar to a given target endpoint.
Two endpoints are considered similar if they contain the **same measure and timeframe**. Do not consider description.

#### **Input:**
- **Target Endpoint (Dictionary):**
  A dictionary containing the following keys:
  - `nctId` (str): Clinical trial identifier.
  - `endpoint` (str): Description of the measured outcome.
  - `endpointID` (str): Unique identifier for the endpoint.

- **Candidate Endpoints (List of Dictionaries):**
  A list of dictionaries where each dictionary contains:
  - `nctId` (str): Clinical trial identifier.
  - `endpoint` (str): Description of the measured outcome.
  - `endpointID` (str): Unique identifier for the endpoint.

#### **Output:**
- **Python List of Similar Endpoint IDs (List[str]):**
  A list containing `endpointID`s of endpoints that are similar to the target.

#### **Similarity Criteria:**
1. **Endpoint Similarity:**
   Two endpoints are considered similar if they contain the same **measure** and **timeframe**.

#### **Example:**
**Target Endpoint:**
```json
{
  "nctId": "NCT02883127",
  "endpoint": "measure: HbA1c, description: noted 3 times during pregnancy, timeFrame: 2 years and 9 months",
  "endpointID": "67dbb1a43817ebedbb0c0e03"
}
```

**Candidate Endpoints:**
```json
[
  {
    "nctId": "NCT02883127",
    "endpoint": "measure: HbA1c, description: noted 3 times during pregnancy, timeFrame: 2 years and 9 months",
    "endpointID": "67dbb1a43817ebedbb0c0e03"
  },
  {
    "nctId": "NCT05702073",
    "endpoint": "Measure: Glycosylated Haemoglobin, Description: Recorded three times throughout pregnancy, TimeFrame: 2 years and 9 months",
    "endpointID": "67dbb1a4dcc1420a76317e9e"
  },
  {
    "nctId": "NCT06415773",
    "endpoint": "measure: Primary Endpoint: Mean change in HbA1c, description: Mean change in HbA1c from baseline to Week 24, timeFrame: 24 Weeks",
    "endpointID": "67dbb1a40e98634061d09119"
  }
]
```

**Expected Output:**
Always follow this JSON response format:
```json
json_object
{
  "response": [
    "67dbb1a43817ebedbb0c0e03",
    "67dbb1a4dcc1420a76317e9e"
  ]
}
```

#### **Notes:**
1. In the sample response, two IDs are considered similar because they share a similar measure and timeframe.
2. In there are no similar endpoints return empty list.
3. JSON object are always enclosed in double quotes ", so never use single quotes for any variable
"""

primary_endpoints_tag_prompt =  """
You are an expert in extracting structured medical information from unstructured text.
Given a clinical trial eligibility endpoint input, extract relevant tags related to:
Tags are keywords related to medical terms like body composition, cancer, renal etc and time frame

### Instructions:
1. Identify and extract all numerical ranges for different medical terms if they are in input.
2. If multiple values exist for a category (e.g., two different HbA1c ranges), include both separately.
3. Convert extracted values into a structured format.
4. Format the output as a JSON object with a list of tags.

### Input Example:
Male or female, aged 18~75 years old;
T2DM and treated with Metformin ≥ 1500mg/day constantly for at least 12 consecutive weeks;
7.5% ≤ HbA1c ≤ 10.0% at screening;
18.5 kg/m2 < BMI < 35.0 kg/m2 at screening;

### Expected Output Format:
{
  "tags": ["Age 18-75", "HbA1c 7.5-10.0", "BMI <35.0"]
}

### Additional Example:
Renal impairment measured as estimated glomerular filtration rate (eGFR) below 60 mL/min/1.73 m^2 as per Chronic Kidney Disease Epidemiology Collaboration formula(CKD-EPI).
Female who is pregnant, breast-feeding or intends to become pregnant or is of child-bearing potential and not using a highly effective contraceptive method.

### Expected Output:
{
  "tags": ["Pregnant", "eGFR < 60 mL/min/1.73 m²"]
}

### Response format:
json_object:
{
  "tags": [
    "tag1",
    "tag2",
    "tag3"
  ]
}

Return the output strictly in JSON format as specified above.
If input string does not have any tags present simply return an empty list.
"""