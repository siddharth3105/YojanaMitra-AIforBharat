# Design Document: Yojana Mitra

## Overview

Yojana Mitra is a serverless, multi-agent AI system built on AWS Bedrock that helps underserved Indians discover and apply for government schemes. The system uses a swarm of specialized agents orchestrated by AWS Bedrock Agents, with RAG-powered knowledge retrieval, voice processing, and multimodal document verification. The architecture is designed to scale to 100M+ users while maintaining sub-5-second response times and 99.9% uptime.

### Key Design Principles

1. **Serverless-First**: All components use AWS serverless services for automatic scaling
2. **Agent Specialization**: Each agent has a focused responsibility with clear interfaces
3. **RAG-Grounded Responses**: All scheme information comes from verified Knowledge Base sources
4. **Multi-Channel Access**: Support for WhatsApp, web, and CSC kiosks through unified API
5. **Language-First Design**: Regional language support is core, not an afterthought
6. **Security by Default**: Encryption, masking, and compliance built into every component

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interfaces                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   WhatsApp   │  │  CSC Kiosk   │  │   Web App    │              │
│  │   Business   │  │  Interface   │  │  (Future)    │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
└─────────┼──────────────────┼──────────────────┼────────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                    ┌────────▼────────┐
                    │   API Gateway   │
                    │   (REST/WS)     │
                    └────────┬────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
    ┌─────▼──────┐                    ┌────────▼────────┐
    │  Lambda:   │                    │   Lambda:       │
    │  Input     │                    │   Output        │
    │  Processor │                    │   Formatter     │
    └─────┬──────┘                    └────────▲────────┘
          │                                    │
          │  ┌─────────────────────────────────┘
          │  │
    ┌─────▼──▼─────────────────────────────────────────┐
    │         AWS Bedrock Agent (Orchestrator)         │
    │  ┌──────────────────────────────────────────┐   │
    │  │         Agent Swarm Coordinator          │   │
    │  └──────────────────────────────────────────┘   │
    │                                                   │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
    │  │Eligibility│ │Explanation│ │  Action  │        │
    │  │  Agent   │ │  Agent    │ │  Agent   │        │
    │  └────┬─────┘ └────┬──────┘ └────┬─────┘        │
    │       │            │             │               │
    └───────┼────────────┼─────────────┼───────────────┘
            │            │             │
            │            │             │
    ┌───────▼────────────▼─────────────▼───────────────┐
    │         AWS Bedrock Knowledge Base                │
    │  ┌──────────────────────────────────────────┐   │
    │  │  Vector Store (OpenSearch Serverless)    │   │
    │  │  - Scheme PDFs (100+ schemes)            │   │
    │  │  - Eligibility criteria                  │   │
    │  │  - Application procedures                │   │
    │  └──────────────────────────────────────────┘   │
    └───────────────────────────────────────────────────┘
            │
    ┌───────▼────────────────────────────────────────┐
    │         Supporting Services                     │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐       │
    │  │Transcribe│ │  Polly   │ │ Textract │       │
    │  │(Voice→  │ │(Text→   │ │  (OCR)   │       │
    │  │ Text)    │ │ Voice)   │ │          │       │
    │  └──────────┘ └──────────┘ └──────────┘       │
    │                                                 │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐       │
    │  │DynamoDB  │ │    S3    │ │EventBridge│      │
    │  │(State)   │ │(Docs)    │ │(Reminders)│      │
    │  └──────────┘ └──────────┘ └──────────┘       │
    └─────────────────────────────────────────────────┘
```

### Agent Swarm Architecture

```
                    ┌─────────────────────────┐
                    │  Bedrock Orchestrator   │
                    │  (Main Agent)           │
                    └───────────┬─────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
        │ Eligibility  │ │Explanation │ │   Action   │
        │    Agent     │ │   Agent    │ │   Agent    │
        │              │ │            │ │            │
        │ - RAG Query  │ │ - Simplify │ │ - OCR      │
        │ - Match      │ │ - Translate│ │ - Verify   │
        │ - Rank       │ │ - Format   │ │ - Generate │
        └──────┬───────┘ └─────┬──────┘ └─────┬──────┘
               │               │               │
               └───────────────┼───────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Proactive Agent    │
                    │  (EventBridge)      │
                    │                     │
                    │  - Schedule         │
                    │  - Notify           │
                    │  - Track            │
                    └─────────────────────┘
```

### Detailed End-to-End Architecture Flow

The following diagram shows the complete data flow from user input through the agent swarm to voice output:

```
YojanaMitra - AWS Bedrock Multi-Agent Architecture
==================================================

User Input Flow → Agent Swarm → Knowledge Base RAG → Voice Output
------------------------------------------------------------------

┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER LAYER                                      │
│                                                                              │
│  👤 Rural Citizens / Farmers / Students                                     │
│     (Voice/Text Input in Hindi/Regional Languages)                          │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   │ Voice/Text Input
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INPUT PROCESSING LAYER                               │
│                                                                              │
│  ┌──────────────────────┐                                                   │
│  │  Amazon Transcribe   │  ◄── Voice Input (Hindi, Tamil, Telugu, etc.)    │
│  │  (Voice → Text)      │                                                   │
│  └──────────┬───────────┘                                                   │
│             │                                                                │
│             ├─────────────► Text Input (Direct)                             │
│             │                                                                │
│             ▼                                                                │
│  ┌──────────────────────┐                                                   │
│  │   API Gateway        │  ◄── WhatsApp / CSC Kiosk / Web                  │
│  │   (REST/WebSocket)   │                                                   │
│  └──────────┬───────────┘                                                   │
│             │                                                                │
└─────────────┼────────────────────────────────────────────────────────────────┘
              │
              │ Normalized Input
              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │         AWS Bedrock Orchestrator Agent                           │      │
│  │         (Claude 3 Sonnet)                                        │      │
│  │                                                                  │      │
│  │  • Analyzes user query                                          │      │
│  │  • Routes to appropriate agents                                 │      │
│  │  • Maintains conversation context                               │      │
│  │  • Coordinates agent responses                                  │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└──────────────┬───────────────────┬───────────────────┬──────────────────────┘
               │                   │                   │
               │                   │                   │
               ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AGENT SWARM LAYER                                    │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │  Eligibility    │  │  Explanation    │  │    Action       │            │
│  │     Agent       │  │     Agent       │  │    Agent        │            │
│  │                 │  │                 │  │                 │            │
│  │ • RAG Query     │  │ • Simplify      │  │ • OCR Docs      │            │
│  │ • Match Profile │  │ • Translate     │  │ • Verify        │            │
│  │ • Rank Schemes  │  │ • Format        │  │ • Generate Form │            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│           │                    │                     │                      │
│           │                    │                     │                      │
└───────────┼────────────────────┼─────────────────────┼──────────────────────┘
            │                    │                     │
            │                    │                     │
            ▼                    │                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      KNOWLEDGE & DATA LAYER                                  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │         AWS Bedrock Knowledge Base (RAG)                         │      │
│  │                                                                  │      │
│  │  ┌────────────────────────────────────────────────────┐         │      │
│  │  │  OpenSearch Serverless (Vector Store)              │         │      │
│  │  │  • 100+ Government Scheme PDFs                     │         │      │
│  │  │  • Eligibility Criteria                            │         │      │
│  │  │  • Application Procedures                          │         │      │
│  │  │  • Titan Embeddings for Semantic Search            │         │      │
│  │  └────────────────────────────────────────────────────┘         │      │
│  │                                                                  │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│           ▲                                                                 │
│           │                                                                 │
│  ┌────────┴────────┐                                                        │
│  │   S3 Bucket     │  ◄── Scheme Documents (PDFs)                          │
│  │  (Scheme PDFs)  │                                                        │
│  └─────────────────┘                                                        │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │  Amazon         │  │   DynamoDB      │  │   S3 Bucket     │            │
│  │  Textract       │  │  (User State &  │  │  (User Docs)    │            │
│  │  (OCR)          │  │   Context)      │  │                 │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   │ Processed Response
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OUTPUT PROCESSING LAYER                              │
│                                                                              │
│  ┌──────────────────────┐                                                   │
│  │   Amazon Polly       │  ◄── Text Response                                │
│  │   (Text → Voice)     │                                                   │
│  │                      │                                                   │
│  │  • Hindi Voice       │                                                   │
│  │  • Regional Voices   │                                                   │
│  │  • Neural TTS        │                                                   │
│  └──────────┬───────────┘                                                   │
│             │                                                                │
│             ▼                                                                │
│  ┌──────────────────────┐                                                   │
│  │   API Gateway        │  ──► WhatsApp / CSC / Web                         │
│  │   (Response)         │                                                   │
│  └──────────────────────┘                                                   │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   │ Voice/Text Output
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER LAYER                                      │
│                                                                              │
│  👤 User receives response in their language                                │
│     (Voice or Text)                                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


PROACTIVE AGENT (Background Process)
=====================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌──────────────────┐         ┌──────────────────┐                         │
│  │  EventBridge     │  ──────►│  Lambda          │                         │
│  │  (Scheduled)     │         │  (Reminder       │                         │
│  │                  │         │   Service)       │                         │
│  │  • 7 days before │         └────────┬─────────┘                         │
│  │  • 3 days before │                  │                                    │
│  │  • 1 day before  │                  │                                    │
│  └──────────────────┘                  ▼                                    │
│                              ┌──────────────────┐                           │
│                              │  Proactive Agent │                           │
│                              │  (Bedrock)       │                           │
│                              └────────┬─────────┘                           │
│                                       │                                     │
│                                       ▼                                     │
│                              ┌──────────────────┐                           │
│                              │   SNS / SQS      │                           │
│                              │  (Notifications) │                           │
│                              └────────┬─────────┘                           │
│                                       │                                     │
│                                       ▼                                     │
│                              👤 User (WhatsApp/SMS)                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Data Flow Steps:**

1. **User Input**: User speaks/types in Hindi or regional language
2. **Voice Processing**: Transcribe converts voice to text (if needed)
3. **API Gateway**: Receives input from WhatsApp/CSC/Web
4. **Orchestration**: Bedrock Orchestrator analyzes query and routes to agents
5. **Agent Swarm**: 
   - Eligibility Agent queries Knowledge Base (RAG on scheme PDFs)
   - Explanation Agent simplifies response in user's language
   - Action Agent processes documents (Textract OCR) and generates forms
6. **Knowledge Base**: RAG retrieval from OpenSearch Serverless with Titan Embeddings
7. **Output Processing**: Polly converts text response to voice
8. **Response Delivery**: API Gateway sends response via WhatsApp/CSC/Web
9. **Proactive Reminders**: EventBridge + Lambda send scheduled notifications

**Hallucination Prevention:**
- All scheme information comes from Knowledge Base (RAG)
- No model-generated scheme details
- Citations to source documents included
- Hybrid search (semantic + keyword) for accuracy
- Confidence scoring on all responses

## Components and Interfaces

### 1. Input Processor (Lambda)

**Responsibility**: Receive and normalize input from all channels (WhatsApp, CSC, Web)

**Interface**:
```typescript
interface InputProcessorRequest {
  channel: 'whatsapp' | 'csc' | 'web';
  userId: string;
  sessionId: string;
  inputType: 'text' | 'voice' | 'image';
  content: string | Buffer;
  language?: string;
  metadata?: {
    phoneNumber?: string;
    cscId?: string;
    location?: string;
  };
}

interface InputProcessorResponse {
  processedInput: {
    text: string;
    language: string;
    intent?: string;
  };
  sessionContext: SessionContext;
  error?: ErrorDetails;
}
```

**AWS Services Used**:
- **Lambda**: Serverless compute for input processing
- **Transcribe**: Voice-to-text conversion for voice inputs
- **Comprehend**: Language detection and intent classification
- **DynamoDB**: Session state storage

**Processing Flow**:
1. Receive input from API Gateway
2. Identify input type (text/voice/image)
3. If voice: Call Transcribe to convert to text
4. Detect language using Comprehend
5. Load session context from DynamoDB
6. Pass to Bedrock Orchestrator

**Justification**: Lambda provides automatic scaling and pay-per-use pricing, ideal for handling variable load from 100M+ users. Transcribe supports all required Indian languages with high accuracy.

### 2. AWS Bedrock Orchestrator (Main Agent)

**Responsibility**: Coordinate agent swarm, maintain conversation context, route requests

**Configuration**:
```yaml
Agent:
  Name: YojanaMitraOrchestrator
  Foundation Model: anthropic.claude-3-sonnet-20240229-v1:0
  Instructions: |
    You are the orchestrator for Yojana Mitra, a system helping Indians access government schemes.
    Coordinate specialized agents to help users discover, understand, and apply for schemes.
    Always respond in the user's preferred language.
    Maintain context across multi-turn conversations.
  
  Action Groups:
    - EligibilityCheck
    - ExplainScheme
    - ProcessDocument
    - GenerateForm
  
  Knowledge Bases:
    - SchemeKnowledgeBase (ID: kb-xxxxx)
```

**Interface**:
```typescript
interface OrchestratorRequest {
  userQuery: string;
  language: string;
  sessionContext: SessionContext;
  availableAgents: string[];
}

interface OrchestratorResponse {
  response: string;
  agentsInvoked: string[];
  nextActions: string[];
  updatedContext: SessionContext;
}
```

**AWS Services Used**:
- **Bedrock Agents**: Orchestration and agent coordination
- **Claude 3 Sonnet**: Foundation model for reasoning and language understanding
- **DynamoDB**: Conversation context storage

**Decision Logic**:
1. Analyze user query and session context
2. Determine which agents are needed
3. Invoke agents in appropriate sequence
4. Aggregate results
5. Format response in user's language
6. Update session context

**Justification**: Bedrock Agents provide built-in orchestration, memory management, and action group coordination. Claude 3 Sonnet offers excellent multilingual capabilities and reasoning for complex eligibility logic.

### 3. Eligibility Agent

**Responsibility**: Match users to eligible schemes using RAG on Knowledge Base

**Action Group Definition**:
```yaml
ActionGroup:
  Name: EligibilityCheck
  Description: Check user eligibility for government schemes
  
  Actions:
    - Name: findEligibleSchemes
      Description: Find schemes matching user profile
      Parameters:
        - age: integer
        - occupation: string
        - income: integer
        - location: string
        - category: string (SC/ST/OBC/General)
        - landOwnership: boolean
        - additionalCriteria: object
      
    - Name: checkSpecificScheme
      Description: Check eligibility for a specific scheme
      Parameters:
        - schemeName: string
        - userProfile: object
```

**Lambda Implementation**:
```typescript
interface EligibilityCheckRequest {
  action: 'findEligibleSchemes' | 'checkSpecificScheme';
  parameters: {
    userProfile: UserProfile;
    schemeName?: string;
  };
}

interface EligibilityCheckResponse {
  eligibleSchemes: Array<{
    schemeName: string;
    confidence: number;
    matchedCriteria: string[];
    missingCriteria: string[];
    benefits: string;
    sourceDocument: string;
  }>;
  reasoning: string;
}
```

**RAG Implementation**:
1. Convert user profile to semantic query
2. Query Knowledge Base with RetrieveAndGenerate API
3. Extract eligibility criteria from retrieved documents
4. Match user profile against criteria
5. Rank schemes by confidence score
6. Return top matches with reasoning

**AWS Services Used**:
- **Bedrock Knowledge Base**: RAG retrieval from scheme documents
- **OpenSearch Serverless**: Vector storage for semantic search
- **Lambda**: Eligibility matching logic
- **Titan Embeddings**: Convert queries to vectors

**Justification**: Knowledge Base ensures responses are grounded in official scheme documents, preventing hallucinations. OpenSearch Serverless provides automatic scaling for vector search.

### 4. Explanation Agent

**Responsibility**: Simplify scheme information into regional languages

**Action Group Definition**:
```yaml
ActionGroup:
  Name: ExplainScheme
  Description: Explain schemes in simple regional language
  
  Actions:
    - Name: simplifyScheme
      Description: Explain scheme in user's language
      Parameters:
        - schemeName: string
        - language: string
        - literacyLevel: string (low/medium/high)
        - focusAreas: array (benefits/eligibility/documents/process)
```

**Lambda Implementation**:
```typescript
interface ExplanationRequest {
  schemeName: string;
  language: string;
  literacyLevel: 'low' | 'medium' | 'high';
  focusAreas: string[];
}

interface ExplanationResponse {
  simplifiedExplanation: {
    title: string;
    summary: string;
    benefits: string[];
    eligibility: string[];
    documents: string[];
    process: string[];
  };
  examples: string[];
  language: string;
}
```

**Processing Flow**:
1. Retrieve scheme details from Knowledge Base
2. Use Claude with language-specific prompt
3. Simplify based on literacy level
4. Translate to target language
5. Add relevant examples
6. Format for voice or text output

**AWS Services Used**:
- **Bedrock (Claude)**: Language simplification and translation
- **Knowledge Base**: Retrieve scheme details
- **Lambda**: Orchestration logic

**Prompt Engineering**:
```
You are explaining government schemes to users with {literacyLevel} literacy in {language}.
Use simple words, short sentences, and concrete examples.
Avoid jargon. If technical terms are needed, explain them simply.
Focus on: {focusAreas}

Scheme Details: {schemeDetails}

Provide explanation in this structure:
1. What is this scheme? (1-2 simple sentences)
2. Who can get it? (simple eligibility)
3. What will you get? (concrete benefits)
4. What documents do you need? (simple list)
5. How to apply? (step-by-step)
```

**Justification**: Claude excels at language simplification and translation. Separating explanation from eligibility allows focused optimization of each agent.

### 5. Action Agent

**Responsibility**: Document processing, verification, and form generation

**Action Group Definition**:
```yaml
ActionGroup:
  Name: ProcessDocument
  Description: Process documents and generate forms
  
  Actions:
    - Name: extractDocumentData
      Description: Extract data from document image
      Parameters:
        - documentImage: string (S3 URI)
        - documentType: string
      
    - Name: verifyDocument
      Description: Verify document authenticity
      Parameters:
        - documentData: object
        - documentType: string
      
    - Name: generateApplicationForm
      Description: Generate pre-filled application form
      Parameters:
        - schemeName: string
        - userData: object
        - documentData: object
```

**Lambda Implementation**:
```typescript
interface DocumentProcessingRequest {
  action: 'extract' | 'verify' | 'generateForm';
  documentImage?: string; // S3 URI
  documentType?: string;
  documentData?: object;
  schemeName?: string;
  userData?: object;
}

interface DocumentProcessingResponse {
  extractedData?: {
    documentType: string;
    fields: Record<string, string>;
    confidence: number;
  };
  verificationResult?: {
    isValid: boolean;
    checks: Array<{
      checkType: string;
      passed: boolean;
      details: string;
    }>;
    confidenceScore: number;
  };
  generatedForm?: {
    formPdfUrl: string;
    prefilledFields: string[];
    missingFields: string[];
  };
}
```

**Document Verification Pipeline**:

```
Image Upload → S3 Storage → Textract OCR → Data Extraction
                                    ↓
                            Format Validation
                                    ↓
                            Checksum Verification
                                    ↓
                            QR Code Validation (if present)
                                    ↓
                            Security Feature Detection
                                    ↓
                            Confidence Scoring
                                    ↓
                    Pass/Fail/Manual Review Decision
```

**Verification Methods**:

1. **OCR Extraction** (Textract):
   - Extract all text fields
   - Identify document structure
   - Extract tables and key-value pairs

2. **Format Validation**:
   - Aadhaar: 12-digit format, Verhoeff checksum
   - PAN: 10-character alphanumeric pattern
   - Ration Card: State-specific format validation

3. **QR Code Validation** (Aadhaar):
   - Decode QR code using Lambda
   - Compare QR data with OCR data
   - Validate digital signature if present

4. **Security Feature Detection**:
   - Hologram detection using image analysis
   - Watermark detection
   - Document edge detection for tampering

5. **Confidence Scoring**:
   ```typescript
   confidenceScore = (
     ocrConfidence * 0.3 +
     formatValidation * 0.2 +
     checksumValidation * 0.2 +
     qrValidation * 0.2 +
     securityFeatures * 0.1
   )
   
   if (confidenceScore >= 0.85) return 'PASS';
   if (confidenceScore >= 0.60) return 'MANUAL_REVIEW';
   return 'FAIL';
   ```

**Form Generation**:
1. Retrieve scheme application form template from S3
2. Map extracted document data to form fields
3. Pre-fill all matching fields
4. Generate PDF using Lambda + PDF library
5. Store in S3 and return signed URL

**AWS Services Used**:
- **Textract**: OCR for document extraction
- **Rekognition**: Security feature detection
- **Lambda**: Verification logic and form generation
- **S3**: Document and form storage
- **Secrets Manager**: Store validation keys/checksums

**Justification**: Textract provides high-accuracy OCR for Indian documents. Rekognition can detect tampering and security features. Separating verification into multiple checks provides defense in depth.

### 6. Proactive Agent

**Responsibility**: Schedule reminders, send notifications, track deadlines

**Architecture**:
```
User Action → DynamoDB Event → EventBridge Rule → Lambda → Notification
                                                      ↓
                                              Schedule Future Events
```

**Implementation**:
```typescript
interface ProactiveAgentEvent {
  eventType: 'APPLICATION_STARTED' | 'DEADLINE_APPROACHING' | 'NEW_SCHEME_MATCH';
  userId: string;
  data: {
    schemeName?: string;
    deadline?: string;
    reminderSchedule?: string[];
    notificationChannel?: 'whatsapp' | 'sms';
  };
}

interface ReminderSchedule {
  userId: string;
  schemeName: string;
  deadline: Date;
  reminders: Array<{
    scheduledTime: Date;
    message: string;
    sent: boolean;
  }>;
}
```

**EventBridge Rules**:
```yaml
Rules:
  - Name: DeadlineReminder7Days
    Schedule: rate(1 day)
    Target: Lambda:CheckUpcomingDeadlines
    
  - Name: DeadlineReminder3Days
    Schedule: rate(6 hours)
    Target: Lambda:CheckUpcomingDeadlines
    
  - Name: DeadlineReminder1Day
    Schedule: rate(1 hour)
    Target: Lambda:CheckUpcomingDeadlines
    
  - Name: NewSchemeCheck
    Schedule: rate(1 day)
    Target: Lambda:CheckNewSchemes
```

**Notification Flow**:
1. EventBridge triggers Lambda on schedule
2. Lambda queries DynamoDB for pending reminders
3. For each reminder due:
   - Format message in user's language
   - Send via WhatsApp Business API or SNS
   - Mark as sent in DynamoDB
4. Log notification delivery

**AWS Services Used**:
- **EventBridge**: Scheduled event triggers
- **Lambda**: Reminder processing logic
- **DynamoDB**: Reminder storage and tracking
- **SNS**: SMS notifications (fallback)
- **SQS**: Queue for WhatsApp message delivery

**Justification**: EventBridge provides reliable scheduled execution. DynamoDB Streams can trigger immediate notifications on state changes. SQS ensures reliable message delivery to WhatsApp.

### 7. Knowledge Base

**Configuration**:
```yaml
KnowledgeBase:
  Name: SchemeKnowledgeBase
  Description: Government scheme documents and eligibility criteria
  
  DataSource:
    Type: S3
    Bucket: yojana-mitra-schemes
    Structure:
      - /schemes/{scheme-id}/
          - scheme-details.pdf
          - eligibility-criteria.pdf
          - application-form.pdf
          - faq.pdf
  
  VectorStore:
    Type: OpenSearch Serverless
    Dimensions: 1536 (Titan Embeddings)
    IndexName: scheme-vectors
  
  ChunkingStrategy:
    Type: FIXED_SIZE
    MaxTokens: 300
    OverlapPercentage: 20
  
  EmbeddingModel: amazon.titan-embed-text-v1
```

**Document Processing Pipeline**:
```
PDF Upload → S3 → Lambda Trigger → Text Extraction → Chunking
                                                         ↓
                                                  Embedding Generation
                                                         ↓
                                                  OpenSearch Indexing
                                                         ↓
                                                  Metadata Tagging
```

**Metadata Schema**:
```typescript
interface SchemeMetadata {
  schemeId: string;
  schemeName: string;
  nameHindi: string;
  nameRegional: Record<string, string>;
  ministry: string;
  category: string[];
  targetBeneficiaries: string[];
  eligibilityCriteria: {
    age?: { min?: number; max?: number };
    income?: { max?: number };
    occupation?: string[];
    location?: string[];
    category?: string[];
  };
  benefits: string;
  lastUpdated: string;
  documentVersion: string;
}
```

**RAG Query Pattern**:
```typescript
// Retrieve and Generate API call
const response = await bedrockAgent.retrieveAndGenerate({
  input: {
    text: userQuery
  },
  retrieveAndGenerateConfiguration: {
    type: 'KNOWLEDGE_BASE',
    knowledgeBaseConfiguration: {
      knowledgeBaseId: 'kb-xxxxx',
      modelArn: 'arn:aws:bedrock:...:anthropic.claude-3-sonnet',
      retrievalConfiguration: {
        vectorSearchConfiguration: {
          numberOfResults: 5,
          overrideSearchType: 'HYBRID' // Semantic + keyword
        }
      },
      generationConfiguration: {
        promptTemplate: {
          textPromptTemplate: `
            You are helping users find government schemes.
            Use ONLY the information in the context below.
            If the answer is not in the context, say so.
            
            Context: $search_results$
            
            Question: $query$
            
            Answer in {language}:
          `
        }
      }
    }
  }
});
```

**AWS Services Used**:
- **Bedrock Knowledge Base**: RAG orchestration
- **OpenSearch Serverless**: Vector storage and search
- **Titan Embeddings**: Text-to-vector conversion
- **S3**: Document storage
- **Lambda**: Document processing and indexing

**Justification**: Knowledge Base provides managed RAG with automatic chunking, embedding, and retrieval. OpenSearch Serverless scales automatically. Hybrid search combines semantic and keyword matching for better accuracy.

### 8. Output Formatter (Lambda)

**Responsibility**: Format responses for different channels and convert text to voice

**Interface**:
```typescript
interface OutputFormatterRequest {
  response: string;
  language: string;
  channel: 'whatsapp' | 'csc' | 'web';
  outputType: 'text' | 'voice' | 'both';
  userId: string;
}

interface OutputFormatterResponse {
  formattedText?: string;
  voiceUrl?: string; // S3 URL for audio file
  metadata: {
    duration?: number;
    format?: string;
  };
}
```

**Processing Flow**:
1. Receive response from Orchestrator
2. Format for target channel:
   - WhatsApp: Break into messages <1600 chars, add emojis
   - CSC: Format with clear sections and headings
   - Web: Add HTML formatting
3. If voice output requested:
   - Call Polly to synthesize speech
   - Store audio in S3
   - Return signed URL
4. Return formatted output

**Polly Configuration**:
```typescript
const pollyParams = {
  Text: responseText,
  OutputFormat: 'mp3',
  VoiceId: getVoiceForLanguage(language), // e.g., 'Aditi' for Hindi
  Engine: 'neural', // Better quality
  LanguageCode: language,
  TextType: 'text'
};

// Language-specific voice mapping
function getVoiceForLanguage(lang: string): string {
  const voiceMap = {
    'hi-IN': 'Aditi',      // Hindi
    'ta-IN': 'Kajal',      // Tamil (if available)
    'te-IN': 'Kajal',      // Telugu
    'bn-IN': 'Aditi',      // Bengali
    'en-IN': 'Aditi'       // English (Indian)
  };
  return voiceMap[lang] || 'Aditi';
}
```

**AWS Services Used**:
- **Lambda**: Formatting logic
- **Polly**: Text-to-speech synthesis
- **S3**: Audio file storage
- **CloudFront**: CDN for audio delivery

**Justification**: Polly supports Indian languages with neural voices for natural sound. Lambda provides flexible formatting logic for different channels.

## Data Models

### User Profile
```typescript
interface UserProfile {
  userId: string;
  phoneNumber?: string;
  preferredLanguage: string;
  literacyLevel: 'low' | 'medium' | 'high';
  demographics: {
    age?: number;
    occupation?: string;
    income?: number;
    location: {
      state: string;
      district?: string;
      pincode?: string;
    };
    category?: 'SC' | 'ST' | 'OBC' | 'General';
    gender?: string;
  };
  documents: Array<{
    documentType: string;
    documentId: string;
    s3Uri: string;
    verified: boolean;
    verificationDate?: string;
  }>;
  schemes: Array<{
    schemeId: string;
    status: 'interested' | 'applied' | 'approved' | 'rejected';
    applicationDate?: string;
    deadline?: string;
  }>;
  createdAt: string;
  updatedAt: string;
}
```

### Session Context
```typescript
interface SessionContext {
  sessionId: string;
  userId: string;
  channel: 'whatsapp' | 'csc' | 'web';
  language: string;
  conversationHistory: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
  }>;
  currentIntent?: string;
  extractedEntities: Record<string, any>;
  activeSchemes: string[];
  pendingActions: string[];
  createdAt: string;
  expiresAt: string;
}
```

### Scheme Document
```typescript
interface SchemeDocument {
  schemeId: string;
  schemeName: string;
  nameTranslations: Record<string, string>;
  ministry: string;
  category: string[];
  description: string;
  eligibility: {
    age?: { min?: number; max?: number };
    income?: { max?: number; currency: string };
    occupation?: string[];
    location?: string[];
    category?: string[];
    gender?: string[];
    customCriteria?: Record<string, any>;
  };
  benefits: {
    type: 'financial' | 'subsidy' | 'service' | 'other';
    amount?: number;
    description: string;
  };
  documents: string[];
  applicationProcess: string[];
  deadlines?: {
    type: 'rolling' | 'fixed';
    date?: string;
    frequency?: string;
  };
  sourceDocuments: string[]; // S3 URIs
  lastUpdated: string;
  version: string;
}
```

### Application Record
```typescript
interface ApplicationRecord {
  applicationId: string;
  userId: string;
  schemeId: string;
  status: 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected';
  submittedDocuments: Array<{
    documentType: string;
    s3Uri: string;
    verificationStatus: 'pending' | 'verified' | 'failed';
  }>;
  generatedFormUri?: string;
  timeline: Array<{
    status: string;
    timestamp: string;
    notes?: string;
  }>;
  reminders: Array<{
    type: string;
    scheduledTime: string;
    sent: boolean;
  }>;
  createdAt: string;
  updatedAt: string;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Input Processing Properties

**Property 1: Multi-language voice transcription**
*For any* voice input in a supported language (Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia), the system should successfully transcribe it to text and route it to the orchestrator.
**Validates: Requirements 1.1, 1.3, 1.5**

**Property 2: Text input acceptance**
*For any* text input in a supported language, the system should accept it directly and route it to the orchestrator without transcription.
**Validates: Requirements 1.2, 1.3**

**Property 3: Language detection and consistency**
*For any* user input, the system should detect the language and maintain that language consistently across all agent responses in the conversation.
**Validates: Requirements 13.1, 13.3**

**Property 4: Language switching**
*For any* conversation where the user switches languages mid-session, all subsequent responses should use the new language.
**Validates: Requirements 13.2**

### Eligibility Matching Properties

**Property 5: RAG-grounded eligibility responses**
*For any* eligibility query, all scheme matches returned should include citations to source documents from the Knowledge Base, ensuring no hallucinated information.
**Validates: Requirements 2.1, 2.2**

**Property 6: Scheme ranking by confidence**
*For any* set of matching schemes, they should be ordered by relevance and eligibility confidence score in descending order.
**Validates: Requirements 2.3**

**Property 7: Eligibility criteria extraction completeness**
*For any* scheme document, the system should extract all specified eligibility criteria fields (age, income, occupation, location, category) when present.
**Validates: Requirements 2.5**

**Property 8: Clarification for ambiguous profiles**
*For any* user profile with missing or ambiguous eligibility information, the system should ask clarifying questions before making eligibility determinations.
**Validates: Requirements 2.6**

### Explanation Properties

**Property 9: Knowledge Base retrieval for explanations**
*For any* scheme explanation request, the information should be retrieved from the Knowledge Base rather than generated from the model's training data.
**Validates: Requirements 3.1**

**Property 10: Language simplification**
*For any* scheme explanation, the output text should have lower complexity (measured by readability metrics) than the source document while preserving key information.
**Validates: Requirements 3.2**

**Property 11: Explanation structure completeness**
*For any* scheme explanation, the response should include all required sections: scheme name, benefits, eligibility, required documents, and application process.
**Validates: Requirements 3.4**

**Property 12: Technical term definitions**
*For any* explanation containing technical terms, those terms should be accompanied by simple definitions or examples.
**Validates: Requirements 3.5**

**Property 13: Regional language output**
*For any* explanation request, the output should be in the user's preferred regional language as specified in their profile or session context.
**Validates: Requirements 3.3**

### Document Processing Properties

**Property 14: Document OCR and type identification**
*For any* uploaded document image (Aadhaar, PAN, ration card, income certificate, caste certificate, land records), the system should extract text via OCR and correctly identify the document type.
**Validates: Requirements 4.1, 4.2, 4.5**

**Property 15: Form field pre-filling**
*For any* document data and application form template, all matching fields should be pre-filled with extracted data, and the mapping should be correct.
**Validates: Requirements 4.3**

**Property 16: PDF form generation**
*For any* form generation request with valid data, the system should produce a valid PDF file that can be opened and printed.
**Validates: Requirements 4.4**

### Document Verification Properties

**Property 17: Multi-method verification pipeline**
*For any* uploaded document, the system should perform all applicable verification checks (OCR, format validation, checksum verification, QR code validation, security feature detection) and assign a confidence score.
**Validates: Requirements 4A.1, 4A.6**

**Property 18: Aadhaar QR code validation**
*For any* Aadhaar card image containing a QR code, the system should decode the QR code and validate that the data matches the OCR-extracted text.
**Validates: Requirements 4A.2**

**Property 19: PAN format and checksum validation**
*For any* PAN card image, the system should validate that the PAN number follows the correct format (5 letters, 4 digits, 1 letter) and passes checksum verification.
**Validates: Requirements 4A.3**

**Property 20: Security feature detection**
*For any* document containing security features (holograms, watermarks), the system should attempt to detect them and include detection results in the confidence score.
**Validates: Requirements 4A.4**

**Property 21: Verification failure reporting**
*For any* document verification that fails, the system should specify which verification checks failed and request alternative documents or manual review.
**Validates: Requirements 4A.5, 4A.7**

### Proactive Agent Properties

**Property 22: Reminder scheduling on application start**
*For any* application started by a user, the system should schedule reminders at 7 days, 3 days, and 1 day before the deadline.
**Validates: Requirements 5.1, 5.4**

**Property 23: Deadline notification delivery**
*For any* scheduled reminder whose time has arrived, the system should send a notification via the user's preferred channel (WhatsApp, SMS).
**Validates: Requirements 5.2**

**Property 24: New scheme proactive matching**
*For any* new scheme added to the Knowledge Base, the system should identify users whose profiles match the eligibility criteria and notify them.
**Validates: Requirements 5.3**

**Property 25: Reminder cancellation on completion**
*For any* user action that completes an application step, the system should cancel all related pending reminders for that step.
**Validates: Requirements 5.5**

### Orchestration Properties

**Property 26: Agent routing and coordination**
*For any* user query, the orchestrator should determine the required agents, execute them in the correct sequence, and pass data between agents correctly.
**Validates: Requirements 6.1, 6.2, 6.3, 6.6**

**Property 27: Graceful agent failure handling**
*For any* agent execution failure, the orchestrator should handle the error gracefully, provide a user-friendly error message, and not crash the conversation.
**Validates: Requirements 6.4, 14.1**

**Property 28: Conversation context persistence**
*For any* multi-turn conversation, the system should maintain context (user profile, conversation history, extracted entities) across all agent interactions.
**Validates: Requirements 6.5, 8.6**

### Knowledge Base Properties

**Property 29: Document indexing on addition**
*For any* new scheme document added to S3, the Knowledge Base should index it for RAG retrieval within the processing window.
**Validates: Requirements 7.2**

**Property 30: Semantic search retrieval**
*For any* semantic query about schemes, the Knowledge Base should return relevant documents ranked by similarity score.
**Validates: Requirements 7.4**

### WhatsApp Integration Properties

**Property 31: WhatsApp multi-modal input handling**
*For any* WhatsApp input (text message, voice note, image), the system should receive it, process it according to type, and route it to the orchestrator.
**Validates: Requirements 8.1, 8.3, 8.4**

**Property 32: WhatsApp response delivery**
*For any* completed processing request from WhatsApp, the system should format the response appropriately for WhatsApp (message length limits, formatting) and send it back to the user.
**Validates: Requirements 8.2, 8.5**

### CSC Kiosk Properties

**Property 33: CSC document scanning**
*For any* document scanned via CSC kiosk hardware, the system should accept and process it through the same document processing pipeline.
**Validates: Requirements 9.3**

**Property 34: CSC form printing**
*For any* form generated at a CSC kiosk, the system should enable direct printing and track the application as CSC-assisted.
**Validates: Requirements 9.4, 9.5**

### Voice Output Properties

**Property 35: Text-to-speech conversion**
*For any* response to a voice user, the system should convert the text to speech using AWS Polly with the correct regional language voice.
**Validates: Requirements 10.1, 10.2**

**Property 36: Long response segmentation**
*For any* response exceeding a length threshold, the system should break it into manageable audio segments for better comprehension.
**Validates: Requirements 10.4**

### Security and Privacy Properties

**Property 37: Data encryption**
*For any* personal information provided by users, the system should encrypt it in transit (TLS) and at rest (KMS).
**Validates: Requirements 12.1**

**Property 38: Sensitive data masking in logs**
*For any* log entry containing sensitive document data (Aadhaar, PAN), the system should mask sensitive fields before writing to logs.
**Validates: Requirements 12.5**

**Property 39: Role-based access control**
*For any* administrative function access attempt, the system should enforce role-based access control and deny unauthorized access.
**Validates: Requirements 12.6**

### Error Handling and Resilience Properties

**Property 40: Service unavailability handling**
*For any* AWS service unavailability, the system should queue requests, notify users of delays, and retry when service is restored.
**Validates: Requirements 14.2**

**Property 41: Transcription failure fallback**
*For any* voice transcription failure, the system should ask the user to repeat or offer to switch to text input.
**Validates: Requirements 14.3**

**Property 42: OCR failure fallback**
*For any* document OCR failure, the system should request a clearer image or offer manual data entry as an alternative.
**Validates: Requirements 14.4**

### Monitoring Properties

**Property 43: Interaction logging**
*For any* user interaction, the system should log it with timestamp, user ID, query, response, agents invoked, and outcome.
**Validates: Requirements 15.1**

**Property 44: Metrics tracking**
*For any* interaction, the system should track relevant metrics (query volume, scheme matches, applications started/completed, response times, error rates).
**Validates: Requirements 15.2, 15.3**

**Property 45: Anomaly alerting**
*For any* detected anomaly (error rate spike, response time degradation, service failure), the system should alert administrators.
**Validates: Requirements 15.5**

### Offline and Resilience Properties

**Property 46: Session state persistence on disconnect**
*For any* connectivity loss during a session, the system should save the conversation state to DynamoDB.
**Validates: Requirements 16.1**

**Property 47: Session recovery on reconnect**
*For any* user reconnection after connectivity loss, the system should restore the session from the last successful interaction.
**Validates: Requirements 16.2**

**Property 48: Offline caching for common queries**
*For any* common scheme query when the system is in offline mode, cached scheme information should be returned.
**Validates: Requirements 16.3**

**Property 49: Degraded mode indication**
*For any* operation in degraded mode (partial service outage), the system should clearly indicate limited functionality to the user.
**Validates: Requirements 16.4**

**Property 50: Critical function prioritization**
*For any* partial outage, the system should prioritize critical functions (eligibility checking, form generation) over non-critical functions (analytics, reporting).
**Validates: Requirements 16.5**

### Language Formatting Properties

**Property 51: Locale-specific formatting**
*For any* output containing dates, numbers, or currency, the system should format them according to the user's language-specific conventions.
**Validates: Requirements 13.5**



## Error Handling

### Error Categories and Strategies

#### 1. Input Processing Errors

**Voice Transcription Failures**:
- **Cause**: Background noise, unclear speech, unsupported accent
- **Detection**: Low confidence score from Transcribe (<0.7)
- **Handling**: 
  - Request user to repeat in quieter environment
  - Offer text input alternative
  - Provide example of clear speech
- **User Message**: "आपकी आवाज़ साफ नहीं सुनाई दी। कृपया शांत जगह से दोबारा बोलें या लिखकर भेजें।" (Your voice was not clear. Please speak again from a quiet place or send text.)

**Language Detection Failures**:
- **Cause**: Mixed language input, code-switching, very short input
- **Detection**: Comprehend returns low confidence or multiple languages
- **Handling**:
  - Ask user to specify preferred language
  - Default to Hindi if no preference available
  - Store preference for future interactions
- **User Message**: "कृपया अपनी भाषा चुनें: हिंदी, தமிழ், తెలుగు..." (Please choose your language: Hindi, Tamil, Telugu...)

#### 2. Eligibility Matching Errors

**No Schemes Found**:
- **Cause**: User profile doesn't match any scheme criteria
- **Detection**: Empty result set from Knowledge Base query
- **Handling**:
  - Suggest related schemes with partial matches
  - Ask clarifying questions to refine profile
  - Provide contact for human assistance
- **User Message**: "आपकी जानकारी से कोई योजना नहीं मिली। क्या आप अपनी उम्र/आय/पेशा बता सकते हैं?" (No schemes found with your information. Can you provide your age/income/occupation?)

**Ambiguous Eligibility**:
- **Cause**: Missing critical information (age, income, location)
- **Detection**: Eligibility agent identifies missing required fields
- **Handling**:
  - Ask specific questions for missing information
  - Explain why information is needed
  - Offer to check multiple scenarios
- **User Message**: "इस योजना के लिए मुझे आपकी उम्र जाननी होगी। आपकी उम्र क्या है?" (For this scheme I need to know your age. What is your age?)

**Knowledge Base Retrieval Failures**:
- **Cause**: OpenSearch service unavailable, network issues
- **Detection**: API timeout or error response
- **Handling**:
  - Retry with exponential backoff (3 attempts)
  - Fall back to cached common schemes
  - Queue request for later processing
  - Notify user of delay
- **User Message**: "अभी सिस्टम धीमा है। कृपया 2 मिनट बाद फिर कोशिश करें।" (System is slow right now. Please try again in 2 minutes.)

#### 3. Document Processing Errors

**OCR Failures**:
- **Cause**: Poor image quality, blur, glare, partial document
- **Detection**: Textract confidence <0.6 or missing key fields
- **Handling**:
  - Provide specific guidance on image quality
  - Show example of good document photo
  - Offer manual data entry alternative
  - Allow multiple upload attempts
- **User Message**: "दस्तावेज़ की फोटो साफ नहीं है। कृपया अच्छी रोशनी में पूरा दस्तावेज़ दिखाकर फिर से फोटो लें।" (Document photo is not clear. Please take photo again showing full document in good light.)

**Document Verification Failures**:
- **Cause**: Invalid format, failed checksum, tampered document
- **Detection**: Verification confidence score <0.6
- **Handling**:
  - Specify which verification checks failed
  - Request alternative document type
  - Flag for manual review if confidence 0.6-0.85
  - Reject if confidence <0.6
- **User Message**: "आधार कार्ड की जानकारी सही नहीं लग रही। कृपया पैन कार्ड या राशन कार्ड भेजें।" (Aadhaar card information doesn't look correct. Please send PAN card or ration card.)

**Form Generation Failures**:
- **Cause**: Missing required fields, invalid data format, template error
- **Detection**: PDF generation exception or validation failure
- **Handling**:
  - Identify missing fields and request from user
  - Validate data format before generation
  - Provide partial form with manual completion instructions
- **User Message**: "फॉर्म बनाने के लिए आपका पता चाहिए। कृपया अपना पूरा पता बताएं।" (To generate form, I need your address. Please provide your complete address.)

#### 4. Agent Orchestration Errors

**Agent Timeout**:
- **Cause**: Agent takes too long to respond (>30 seconds)
- **Detection**: Lambda timeout or Bedrock agent timeout
- **Handling**:
  - Cancel long-running agent
  - Return partial results if available
  - Offer to continue later
  - Log for investigation
- **User Message**: "यह थोड़ा समय ले रहा है। मैं जानकारी इकट्ठा कर रहा हूं और जल्द ही जवाब दूंगा।" (This is taking some time. I am gathering information and will respond soon.)

**Agent Failure**:
- **Cause**: Lambda error, model error, dependency failure
- **Detection**: Exception thrown by agent
- **Handling**:
  - Log error with full context
  - Attempt alternative agent if available
  - Provide graceful degradation
  - Offer human assistance
- **User Message**: "माफ़ करें, कुछ गड़बड़ हो गई। कृपया फिर से कोशिश करें या हमें फोन करें: 1800-XXX-XXXX" (Sorry, something went wrong. Please try again or call us: 1800-XXX-XXXX)

**Context Loss**:
- **Cause**: Session expired, DynamoDB failure, state corruption
- **Detection**: Missing session data in DynamoDB
- **Handling**:
  - Start fresh conversation
  - Apologize for interruption
  - Offer to quickly recap previous interaction
- **User Message**: "माफ़ करें, आपकी पिछली बातचीत का डेटा नहीं मिला। कृपया फिर से शुरू करें।" (Sorry, your previous conversation data was not found. Please start again.)

#### 5. External Service Errors

**AWS Service Outages**:
- **Cause**: Bedrock, Transcribe, Polly, Textract unavailable
- **Detection**: Service health check failure or API error
- **Handling**:
  - Queue requests in SQS for later processing
  - Provide estimated wait time
  - Send notification when service restored
  - Fall back to cached data where possible
- **User Message**: "अभी सिस्टम में तकनीकी समस्या है। आपका अनुरोध सुरक्षित है और जल्द ही प्रोसेस होगा।" (There is a technical issue in the system right now. Your request is safe and will be processed soon.)

**WhatsApp API Failures**:
- **Cause**: Rate limiting, API downtime, invalid webhook
- **Detection**: HTTP 429 or 5xx errors from WhatsApp
- **Handling**:
  - Retry with exponential backoff
  - Queue messages for batch delivery
  - Fall back to SMS if critical
  - Log for monitoring
- **User Message**: (Sent via SMS) "WhatsApp में समस्या है। आपका जवाब SMS से भेजा गया है।" (There is an issue with WhatsApp. Your response was sent via SMS.)

#### 6. Data Validation Errors

**Invalid User Input**:
- **Cause**: Malformed data, out-of-range values, injection attempts
- **Detection**: Input validation rules
- **Handling**:
  - Reject invalid input
  - Provide specific validation error
  - Show example of valid input
  - Sanitize before processing
- **User Message**: "उम्र 0 से 120 के बीच होनी चाहिए। कृपया सही उम्र बताएं।" (Age should be between 0 and 120. Please provide correct age.)

**Missing Required Fields**:
- **Cause**: User doesn't provide required information
- **Detection**: Field validation in form generation
- **Handling**:
  - List all missing fields
  - Explain why each is needed
  - Offer to collect one at a time
- **User Message**: "फॉर्म भरने के लिए ये जानकारी चाहिए: 1) आधार नंबर 2) मोबाइल नंबर 3) पता" (To fill the form, this information is needed: 1) Aadhaar number 2) Mobile number 3) Address)

### Error Logging and Monitoring

**Structured Error Logging**:
```typescript
interface ErrorLog {
  timestamp: string;
  errorId: string;
  errorType: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  userId: string;
  sessionId: string;
  agent: string;
  errorMessage: string;
  stackTrace?: string;
  context: {
    userQuery?: string;
    agentState?: object;
    awsRequestId?: string;
  };
  resolution: string;
  userImpact: string;
}
```

**CloudWatch Alarms**:
- Error rate >5% in 5-minute window → Alert on-call engineer
- Agent timeout rate >10% → Alert DevOps team
- Knowledge Base query latency >3s → Alert infrastructure team
- Document verification failure rate >20% → Alert ML team

**Error Metrics Dashboard**:
- Total errors by type (last 24 hours)
- Error rate trend (last 7 days)
- Top failing agents
- User-facing error frequency
- Mean time to resolution

### Graceful Degradation Strategy

**Priority Levels**:
1. **Critical**: Eligibility checking, form generation, user authentication
2. **High**: Scheme explanations, document verification, notifications
3. **Medium**: Voice synthesis, analytics, reporting
4. **Low**: Proactive recommendations, usage statistics

**Degradation Rules**:
- If Knowledge Base unavailable → Use cached top 20 schemes
- If Transcribe unavailable → Text-only mode
- If Polly unavailable → Text responses only
- If Textract unavailable → Manual data entry
- If Bedrock unavailable → Queue requests, provide ETA

## Testing Strategy

### Dual Testing Approach

The testing strategy combines **unit testing** for specific examples and edge cases with **property-based testing** for universal correctness properties. Both approaches are complementary and necessary for comprehensive coverage.

**Unit Tests**: Focus on specific examples, integration points, and edge cases
**Property Tests**: Verify universal properties across randomized inputs (minimum 100 iterations per test)

### Property-Based Testing Framework

**Framework Selection**: 
- **Python**: Use `hypothesis` library
- **TypeScript/JavaScript**: Use `fast-check` library
- **Java**: Use `jqwik` library

**Configuration**:
```python
# Python example with hypothesis
from hypothesis import given, settings, strategies as st

@settings(max_examples=100)  # Minimum 100 iterations
@given(
    language=st.sampled_from(['hi-IN', 'ta-IN', 'te-IN', 'bn-IN', 'mr-IN']),
    voice_input=st.text(min_size=10, max_size=500)
)
def test_voice_transcription_property(language, voice_input):
    """
    Feature: yojana-mitra, Property 1: Multi-language voice transcription
    For any voice input in a supported language, the system should 
    successfully transcribe it to text and route it to the orchestrator.
    """
    # Test implementation
    pass
```

### Test Organization

#### 1. Input Processing Tests

**Unit Tests**:
- Test specific voice samples in each language
- Test edge cases: empty input, very long input, special characters
- Test language detection with mixed input
- Test session context creation

**Property Tests**:
- **Property 1**: Voice transcription across all languages
- **Property 2**: Text input acceptance
- **Property 3**: Language detection consistency
- **Property 4**: Language switching behavior

**Test Data**:
- Sample voice recordings in 10 languages
- Edge case inputs: silence, noise, music, multiple speakers
- Text samples with emojis, special characters, code-switching

#### 2. Eligibility Matching Tests

**Unit Tests**:
- Test specific scheme matches (PM-KISAN for farmers)
- Test no-match scenarios
- Test partial match scenarios
- Test edge cases: boundary ages, income thresholds

**Property Tests**:
- **Property 5**: RAG grounding (all responses have citations)
- **Property 6**: Scheme ranking order
- **Property 7**: Criteria extraction completeness
- **Property 8**: Clarification for ambiguous profiles

**Test Data**:
- 100+ scheme documents with varied eligibility criteria
- User profiles covering all demographics
- Edge cases: age 0, age 120, income 0, income max

**Generators**:
```python
@st.composite
def user_profile_generator(draw):
    return {
        'age': draw(st.integers(min_value=0, max_value=120)),
        'income': draw(st.integers(min_value=0, max_value=10000000)),
        'occupation': draw(st.sampled_from(['farmer', 'student', 'worker', 'unemployed'])),
        'location': draw(st.sampled_from(['UP', 'Bihar', 'MP', 'Rajasthan'])),
        'category': draw(st.sampled_from(['SC', 'ST', 'OBC', 'General']))
    }
```

#### 3. Explanation Tests

**Unit Tests**:
- Test specific scheme explanations
- Test simplification of complex terms
- Test translation accuracy for known phrases
- Test structure completeness

**Property Tests**:
- **Property 9**: Knowledge Base retrieval
- **Property 10**: Language simplification (readability metrics)
- **Property 11**: Explanation structure completeness
- **Property 12**: Technical term definitions
- **Property 13**: Regional language output

**Readability Metrics**:
```python
def calculate_readability(text, language):
    """Calculate readability score (lower = simpler)"""
    # Use language-specific readability formulas
    # Hindi: Average word length, sentence length
    # English: Flesch-Kincaid grade level
    pass

def test_simplification_property(scheme_text):
    explanation = explanation_agent.simplify(scheme_text, literacy='low')
    assert calculate_readability(explanation) < calculate_readability(scheme_text)
```

#### 4. Document Processing Tests

**Unit Tests**:
- Test specific document types (sample Aadhaar, PAN, ration card)
- Test poor quality images
- Test partial documents
- Test tampered documents

**Property Tests**:
- **Property 14**: OCR and type identification
- **Property 15**: Form field pre-filling accuracy
- **Property 16**: PDF generation validity
- **Property 17-21**: Verification pipeline properties

**Test Data**:
- 100+ sample documents (real anonymized or synthetic)
- Degraded images: blur, glare, rotation, partial
- Invalid documents: wrong format, failed checksum

**Document Generators**:
```python
@st.composite
def aadhaar_generator(draw):
    """Generate synthetic Aadhaar card data"""
    digits = draw(st.lists(st.integers(0, 9), min_size=12, max_size=12))
    # Apply Verhoeff checksum algorithm
    return {
        'number': ''.join(map(str, digits)),
        'name': draw(st.text(min_size=5, max_size=50)),
        'dob': draw(st.dates(min_value=date(1920, 1, 1))),
        'address': draw(st.text(min_size=20, max_size=200))
    }
```

#### 5. Orchestration Tests

**Unit Tests**:
- Test specific agent sequences (eligibility → explanation → form)
- Test single agent invocations
- Test agent failure scenarios
- Test context passing between agents

**Property Tests**:
- **Property 26**: Agent routing and coordination
- **Property 27**: Graceful failure handling
- **Property 28**: Context persistence

**Mock Agents**:
```python
class MockAgent:
    def __init__(self, should_fail=False, delay=0):
        self.should_fail = should_fail
        self.delay = delay
        self.invocation_count = 0
    
    def invoke(self, input_data):
        self.invocation_count += 1
        time.sleep(self.delay)
        if self.should_fail:
            raise AgentException("Mock failure")
        return {"result": "success", "data": input_data}
```

#### 6. Integration Tests

**End-to-End Flows**:
- WhatsApp voice → eligibility check → explanation → form generation
- CSC kiosk → document scan → verification → form print
- Multi-turn conversation with context preservation
- Error recovery and retry flows

**Load Testing**:
- Simulate 10,000 concurrent users
- Test auto-scaling behavior
- Measure response time percentiles (p50, p95, p99)
- Test Knowledge Base query performance

**Chaos Engineering**:
- Randomly fail agents during execution
- Simulate AWS service outages
- Test queue-based recovery
- Verify graceful degradation

### Test Coverage Goals

**Code Coverage**: Minimum 80% line coverage, 70% branch coverage
**Property Coverage**: All 51 correctness properties implemented as tests
**Integration Coverage**: All critical user flows tested end-to-end
**Language Coverage**: All 10 supported languages tested
**Document Coverage**: All 6 document types tested

### Continuous Testing

**Pre-commit Hooks**:
- Run unit tests (<5 minutes)
- Run linting and type checking
- Run security scanning

**CI/CD Pipeline**:
- Run all unit tests (10-15 minutes)
- Run property tests with 100 iterations (20-30 minutes)
- Run integration tests (15-20 minutes)
- Run security and compliance scans
- Deploy to staging on main branch
- Run smoke tests in staging
- Manual approval for production

**Monitoring in Production**:
- Synthetic transactions every 5 minutes
- Real user monitoring (RUM)
- Error rate tracking
- Performance regression detection
- A/B testing for model improvements

### Test Data Management

**Synthetic Data Generation**:
- Use Faker library for Indian names, addresses, phone numbers
- Generate realistic scheme documents with varied criteria
- Create document images with controlled quality degradation

**Anonymized Real Data**:
- Collect real user queries (with consent) for testing
- Anonymize PII before use in tests
- Use for improving model accuracy

**Test Data Refresh**:
- Regenerate synthetic data monthly
- Update scheme documents when government releases new versions
- Refresh language samples to cover new dialects/variations

### Property Test Tagging Convention

Every property-based test MUST include a comment tag referencing the design document:

```python
def test_property_5_rag_grounding():
    """
    Feature: yojana-mitra, Property 5: RAG-grounded eligibility responses
    For any eligibility query, all scheme matches returned should include 
    citations to source documents from the Knowledge Base.
    Validates: Requirements 2.1, 2.2
    """
    pass
```

This ensures traceability from requirements → design properties → test implementation.

## Deployment Architecture

### AWS Services Summary

| Service | Purpose | Justification |
|---------|---------|---------------|
| **Bedrock Agents** | Agent orchestration | Managed multi-agent coordination with built-in memory |
| **Bedrock Knowledge Base** | RAG for schemes | Prevents hallucinations, automatic chunking and indexing |
| **Claude 3 Sonnet** | Foundation model | Excellent multilingual support, reasoning capability |
| **Titan Embeddings** | Vector generation | Cost-effective, good performance for semantic search |
| **OpenSearch Serverless** | Vector storage | Auto-scaling, managed service, hybrid search |
| **Lambda** | Compute | Serverless, auto-scaling, pay-per-use |
| **API Gateway** | API management | REST/WebSocket support, throttling, authentication |
| **Transcribe** | Voice-to-text | Supports 10 Indian languages, high accuracy |
| **Polly** | Text-to-speech | Neural voices for natural sound, Indian language support |
| **Textract** | Document OCR | High accuracy for Indian documents, table extraction |
| **Rekognition** | Security features | Tamper detection, hologram detection |
| **DynamoDB** | State storage | Serverless, low latency, auto-scaling |
| **S3** | Document storage | Durable, cost-effective, lifecycle policies |
| **EventBridge** | Scheduled events | Reliable cron-like scheduling for reminders |
| **SQS** | Message queuing | Reliable message delivery, retry logic |
| **SNS** | Notifications | SMS fallback for WhatsApp failures |
| **CloudWatch** | Monitoring | Logs, metrics, alarms, dashboards |
| **Secrets Manager** | Secrets storage | Secure storage for API keys, checksums |
| **KMS** | Encryption | Data encryption at rest |
| **CloudFront** | CDN | Fast audio file delivery for voice responses |

### Scalability Considerations

**Auto-Scaling**:
- Lambda: Automatic concurrency scaling to 1000+ concurrent executions
- DynamoDB: On-demand capacity mode for unpredictable traffic
- OpenSearch Serverless: Automatic scaling based on query load
- API Gateway: Handles millions of requests per second

**Cost Optimization**:
- Use Lambda reserved concurrency for predictable workloads
- Implement S3 lifecycle policies (delete documents after 90 days)
- Use CloudFront caching for static content
- Optimize Bedrock model selection (Titan for simple tasks, Claude for complex)

**Performance Optimization**:
- Cache common scheme queries in DynamoDB (TTL 24 hours)
- Use Lambda SnapStart for faster cold starts
- Implement connection pooling for DynamoDB
- Use parallel agent invocation where possible

### Security Architecture

**Authentication & Authorization**:
- WhatsApp: Verify webhook signatures
- CSC: OAuth 2.0 with CSC identity provider
- Admin: Cognito user pools with MFA

**Data Protection**:
- TLS 1.3 for all data in transit
- KMS encryption for all data at rest
- VPC endpoints for private AWS service access
- No public internet access for Lambda functions

**Compliance**:
- GDPR-like data protection (Indian context)
- Data residency in India region (ap-south-1)
- Audit logging for all data access
- Regular security assessments

## Conclusion

This design provides a comprehensive, scalable, and secure architecture for YojanaMitra using AWS Bedrock's multi-agent capabilities. The system is designed to handle 100M+ users while maintaining sub-5-second response times and providing accurate, hallucination-free information about government schemes. The property-based testing strategy ensures correctness across all supported languages and use cases, while the error handling approach provides graceful degradation and clear user communication.
