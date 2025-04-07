# Slices Clinical Trials

## Overview

This service provides a semantic search API for clinical trial documents, enabling researchers to find relevant trials based on multiple criteria. The system uses embeddings and weighted similarity scoring to retrieve the most relevant documents matching the input parameters.

Key features:
- Semantic search across clinical trial documents
- Customizable weighting for different search criteria
- Advanced filtering capabilities
- Structured response format with similarity scoring

## API Documentation

### Base URL
All endpoints are prefixed with `/api/v1/ml`

### Core Endpoint: Document Search

**Endpoint:** `POST /search_documents`

Searches for clinical trial documents based on multiple criteria with semantic matching.

#### Request Parameters

The endpoint accepts a JSON body with the following structure:

```json
{
  "userName": "string",
  "ecid": "string",
  "rationale": "string",
  "condition": "string",
  "inclusionCriteria": "string",
  "exclusionCriteria": "string",
  "efficacyEndpoints": "string",
  "title": "string",
  "weights": {
    "rationale": float,
    "condition": float,
    "inclusionCriteria": float,
    "exclusionCriteria": float,
    "trialOutcomes": float,
    "title": float
  },
  "phase": ["string"],
  "country": ["string"],
  "countryLogic": "string",
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "sponsor": "string",
  "sampleSizeMin": integer,
  "sampleSizeMax": integer
}
```

#### Search Criteria

The service searches using these key fields:
- Rationale
- Medical condition
- Inclusion/exclusion criteria
- Trial outcomes
- Document title

Each field is converted to embeddings and used for semantic similarity matching.

#### Filtering Options

Results can be filtered by:
- Trial phase
- Country/location (with AND/OR logic)
- Date range
- Sponsor type
- Sample size range

#### Weighting System

The similarity scoring uses customizable weights for each search field, allowing users to prioritize certain criteria over others.

#### Response Format

The API returns a standardized response:

```json
{
  "success": boolean,
  "status_code": integer,
  "data": [
    {
      "id": "string",
      "similarity_scores": {
        "rationale": float,
        "condition": float,
        // other fields...
      },
      "weighted_similarity_score": float,
      // document metadata...
    }
  ],
  "message": "string"
}
```

Documents are returned in descending order of their weighted similarity score.

## Technical Implementation

### Core Components

1. **Embedding Generation**:
   - Input criteria are converted to embeddings for semantic search

2. **Vector Search**:
   - Uses Pinecone for efficient similarity matching

3. **Document Processing**:
   - Combines results from multiple criteria searches
   - Ensures document uniqueness while preserving highest scores

4. **Scoring System**:
   - Calculates weighted similarity scores based on user preferences
   - Normalizes scores across different criteria

5. **Filtering Pipeline**:
   - Applies post-search filters to refine results

### Error Handling

The service includes comprehensive error handling:
- Input validation
- Search operation failures
- Database errors
- Unexpected exceptions

All errors return structured responses with appropriate HTTP status codes.

## Getting Started

### Prerequisites

- Python 3.8+
- FastAPI
- Pinecone client
- Additional dependencies (see pyproject.toml)

### Installation

1. Clone the repository
2. Install dependencies: `pip install poetry` `poetry install`
3. Configure environment variables
4. Start the service: `uvicorn main:app --reload`
