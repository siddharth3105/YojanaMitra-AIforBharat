# Requirements Document: Yojana Mitra

## Introduction

Yojana Mitra is an AWS Bedrock-powered multi-agent swarm system designed to help underserved Indians discover, understand, and apply for 100+ government schemes. The system addresses the critical problem that 70-80% of eligible citizens miss benefits due to complex portals, language barriers, and form friction. By providing voice and text input capabilities with specialized AI agents, the system aims to unlock trillions in benefits and scale to 100M+ users via WhatsApp and Common Service Centers (CSC).

## Glossary

- **System**: The Yojana Mitra multi-agent swarm system
- **User**: An Indian citizen seeking government scheme information or assistance
- **Eligibility_Agent**: The agent responsible for matching users to eligible schemes using RAG
- **Explanation_Agent**: The agent that simplifies scheme information in regional languages
- **Action_Agent**: The agent that handles document processing and form generation
- **Proactive_Agent**: The agent that sends reminders and notifications
- **Orchestrator**: The AWS Bedrock Agent that coordinates the agent swarm
- **Knowledge_Base**: AWS Bedrock Knowledge Base containing scheme PDFs and documentation
- **Scheme**: A government benefit program or welfare initiative
- **CSC**: Common Service Center - government-run kiosks for digital services
- **RAG**: Retrieval Augmented Generation for hallucination-free responses
- **Regional_Language**: Hindi or other Indian regional languages (Tamil, Telugu, Bengali, etc.)

## Requirements

### Requirement 1: Voice and Text Input Processing

**User Story:** As a rural citizen with low literacy (मैं एक ग्रामीण नागरिक हूं जिसे पढ़ना-लिखना कम आता है), I want to interact with the system using voice in my regional language (मैं अपनी भाषा में बोलकर योजनाओं के बारे में जानना चाहता हूं), so that I can access scheme information without reading complex text.

**Example:** "मुझे किसान योजना के बारे में बताओ" (Tell me about farmer schemes) or "मेरे लिए कौन सी योजना है?" (Which scheme is for me?)

#### Acceptance Criteria

1. WHEN a user provides voice input in Hindi or a regional language, THE System SHALL transcribe it to text using AWS Transcribe
2. WHEN a user provides text input, THE System SHALL accept it directly for processing
3. WHEN transcription is complete, THE System SHALL route the input to the Orchestrator for agent coordination
4. WHEN voice input contains background noise or unclear speech, THE System SHALL request clarification from the user
5. THE System SHALL support Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, and Odia languages

### Requirement 2: Eligibility Matching via RAG

**User Story:** As a farmer (मैं एक किसान हूं), I want to know which schemes I am eligible for based on my situation (मेरे लिए कौन सी योजनाएं हैं), so that I don't waste time on schemes I cannot access.

**Example:** "मेरे पास 2 एकड़ जमीन है और मेरी उम्र 45 साल है" (I have 2 acres of land and I am 45 years old) - System should match PM-KISAN, crop insurance, and other relevant schemes.

#### Acceptance Criteria

1. WHEN a user describes their situation, THE Eligibility_Agent SHALL query the Knowledge_Base for relevant schemes
2. WHEN matching schemes, THE Eligibility_Agent SHALL use RAG to ensure responses are grounded in official scheme documents
3. WHEN multiple schemes match, THE Eligibility_Agent SHALL rank them by relevance and eligibility confidence
4. WHEN no schemes match, THE Eligibility_Agent SHALL inform the user and suggest related schemes
5. THE Eligibility_Agent SHALL extract eligibility criteria from scheme PDFs including age, income, occupation, location, and category requirements
6. WHEN eligibility criteria are ambiguous, THE Eligibility_Agent SHALL ask clarifying questions to the user

### Requirement 3: Scheme Explanation in Regional Languages

**User Story:** As a low-literacy user (मुझे ज्यादा पढ़ना नहीं आता), I want scheme details explained in simple Hindi (मुझे आसान भाषा में समझाओ), so that I can understand complex government terminology.

**Example:** Instead of "आर्थिक रूप से कमजोर वर्ग के लिए आवास योजना" (Housing scheme for economically weaker sections), explain as "गरीब परिवारों को घर बनाने के लिए पैसे मिलेंगे" (Poor families will get money to build houses).

#### Acceptance Criteria

1. WHEN a user requests scheme details, THE Explanation_Agent SHALL retrieve the scheme information from the Knowledge_Base
2. WHEN explaining schemes, THE Explanation_Agent SHALL simplify complex terminology into plain language
3. WHEN generating explanations, THE Explanation_Agent SHALL use the user's preferred regional language
4. THE Explanation_Agent SHALL structure explanations to include scheme name, benefits, eligibility, required documents, and application process
5. WHEN technical terms are unavoidable, THE Explanation_Agent SHALL provide simple definitions or examples

### Requirement 4: Document Processing and Form Generation

**User Story:** As a citizen applying for a scheme (मैं योजना के लिए आवेदन करना चाहता हूं), I want to scan my documents and get a pre-filled application form (मैं अपने दस्तावेज़ की फोटो खींचकर फॉर्म भरना चाहता हूं), so that I can complete applications quickly without manual data entry.

**Example:** User takes photo of Aadhaar card → System extracts name, address, DOB → Pre-fills application form for PM-KISAN scheme.

#### Acceptance Criteria

1. WHEN a user uploads a document image, THE Action_Agent SHALL process it using OCR to extract text
2. WHEN document text is extracted, THE Action_Agent SHALL identify document type (Aadhaar, PAN, income certificate, etc.)
3. WHEN generating application forms, THE Action_Agent SHALL pre-fill fields using extracted document data
4. WHEN form generation is complete, THE Action_Agent SHALL produce a PDF draft for user review
5. THE Action_Agent SHALL support common document types including Aadhaar, PAN, ration card, income certificate, caste certificate, and land records
6. WHEN document quality is poor, THE Action_Agent SHALL request a clearer image from the user

### Requirement 4A: Multimodal Document Verification

**User Story:** As a scheme administrator, I want to verify document authenticity using multiple verification methods, so that we can prevent fraud and ensure only eligible citizens receive benefits.

**Example:** User submits Aadhaar card image → System performs OCR + checks QR code + validates format + cross-references with masked Aadhaar database (if available).

#### Acceptance Criteria

1. WHEN a document is uploaded, THE Action_Agent SHALL perform multiple verification checks including OCR, format validation, and checksum verification
2. WHEN an Aadhaar card is submitted, THE Action_Agent SHALL validate the QR code if present
3. WHEN a PAN card is submitted, THE Action_Agent SHALL validate the PAN format and checksum
4. WHEN documents contain security features (holograms, watermarks), THE Action_Agent SHALL attempt to detect them using image analysis
5. WHEN verification fails, THE Action_Agent SHALL specify which checks failed and request alternative documents
6. THE Action_Agent SHALL assign a confidence score to each document verification
7. WHEN confidence score is below threshold, THE Action_Agent SHALL flag for manual review or request additional verification

### Requirement 5: Proactive Notifications and Reminders

**User Story:** As a scheme applicant (मैंने योजना के लिए आवेदन किया है), I want to receive reminders about application deadlines and document submissions (मुझे याद दिलाओ कि मुझे क्या करना है), so that I don't miss important dates.

**Example:** "आपको 3 दिन में आय प्रमाण पत्र जमा करना है" (You need to submit income certificate in 3 days) or "नई किसान योजना शुरू हुई है, आप पात्र हैं" (New farmer scheme launched, you are eligible).

#### Acceptance Criteria

1. WHEN a user starts an application, THE Proactive_Agent SHALL schedule reminders for key deadlines
2. WHEN a deadline approaches, THE Proactive_Agent SHALL send notifications via the user's preferred channel
3. WHEN new schemes matching user profile are launched, THE Proactive_Agent SHALL notify the user
4. THE Proactive_Agent SHALL send reminders 7 days, 3 days, and 1 day before deadlines
5. WHEN a user completes an action, THE Proactive_Agent SHALL cancel related reminders

### Requirement 6: Agent Orchestration and Coordination

**User Story:** As a system architect, I want agents to work together seamlessly, so that users receive coherent and complete assistance.

#### Acceptance Criteria

1. WHEN a user query is received, THE Orchestrator SHALL determine which agents are needed
2. WHEN multiple agents are required, THE Orchestrator SHALL coordinate their execution in the correct sequence
3. WHEN an agent completes its task, THE Orchestrator SHALL pass results to the next agent or return to the user
4. WHEN an agent fails, THE Orchestrator SHALL handle the error gracefully and inform the user
5. THE Orchestrator SHALL maintain conversation context across multiple agent interactions
6. WHEN agents need to share information, THE Orchestrator SHALL facilitate data passing between them

### Requirement 7: Knowledge Base Management

**User Story:** As a system administrator, I want scheme information to be automatically updated, so that users always receive current and accurate information.

#### Acceptance Criteria

1. THE System SHALL store scheme PDFs and documentation in the Knowledge_Base
2. WHEN new scheme documents are added, THE Knowledge_Base SHALL index them for RAG retrieval
3. WHEN scheme information is updated, THE Knowledge_Base SHALL reflect changes within 24 hours
4. THE Knowledge_Base SHALL support semantic search across scheme documents
5. THE Knowledge_Base SHALL maintain version history of scheme documents

### Requirement 8: WhatsApp Integration

**User Story:** As a rural user without smartphone apps (मेरे पास सिर्फ WhatsApp है), I want to access the system via WhatsApp (मैं WhatsApp से योजना की जानकारी लेना चाहता हूं), so that I can use a familiar platform.

**Example:** User sends WhatsApp message "प्रधानमंत्री आवास योजना" → System responds with eligibility criteria and application steps in Hindi.

#### Acceptance Criteria

1. WHEN a user sends a WhatsApp message, THE System SHALL receive and process it
2. WHEN processing is complete, THE System SHALL send responses back via WhatsApp
3. THE System SHALL support WhatsApp text messages, voice notes, and image uploads
4. WHEN a user sends a voice note, THE System SHALL transcribe it and process as voice input
5. WHEN sending responses, THE System SHALL format them appropriately for WhatsApp display
6. THE System SHALL maintain conversation state across WhatsApp sessions

### Requirement 9: CSC Kiosk Integration

**User Story:** As a CSC operator (मैं CSC केंद्र चलाता हूं), I want to help citizens access the system through my kiosk (मैं गांव के लोगों की मदद करना चाहता हूं), so that I can serve users without smartphones.

**Example:** Elderly farmer visits CSC → Operator helps them check eligibility for pension scheme → System guides through document scanning → Generates application form for printing.

#### Acceptance Criteria

1. WHEN accessed from a CSC kiosk, THE System SHALL provide a simplified web interface
2. WHEN a CSC operator assists a user, THE System SHALL support operator-mediated interactions
3. THE System SHALL allow document scanning via kiosk hardware
4. WHEN forms are generated at a CSC, THE System SHALL enable direct printing
5. THE System SHALL track CSC-assisted applications for monitoring and support

### Requirement 10: Voice Response Generation

**User Story:** As a low-literacy user (मुझे पढ़ना नहीं आता), I want to hear responses in my language (मुझे सुनकर समझना आसान है), so that I can understand without reading.

**Example:** System speaks: "आपको प्रधानमंत्री किसान सम्मान निधि योजना मिल सकती है। इसमें साल में 6000 रुपये मिलते हैं। आपको आधार कार्ड और जमीन के कागज चाहिए।" (You can get PM-KISAN scheme. You will receive 6000 rupees per year. You need Aadhaar card and land documents.)

#### Acceptance Criteria

1. WHEN generating responses for voice users, THE System SHALL convert text to speech using AWS Polly
2. WHEN synthesizing speech, THE System SHALL use the user's preferred regional language
3. THE System SHALL use natural-sounding voices appropriate for the target language
4. WHEN responses are long, THE System SHALL break them into manageable audio segments
5. WHEN technical terms are spoken, THE System SHALL pronounce them clearly and correctly

### Requirement 11: Scalability and Performance

**User Story:** As a product manager, I want the system to handle 100M+ users, so that we can serve all eligible citizens across India.

#### Acceptance Criteria

1. THE System SHALL support concurrent requests from at least 100,000 users
2. WHEN user load increases, THE System SHALL scale automatically using serverless architecture
3. WHEN processing requests, THE System SHALL respond within 5 seconds for 95% of queries
4. THE System SHALL maintain 99.9% uptime during business hours
5. WHEN Knowledge_Base is queried, THE System SHALL return results within 2 seconds

### Requirement 12: Data Privacy and Security

**User Story:** As a citizen, I want my personal information protected, so that my data is not misused.

#### Acceptance Criteria

1. WHEN users provide personal information, THE System SHALL encrypt it in transit and at rest
2. THE System SHALL comply with Indian data protection regulations and guidelines
3. WHEN storing documents, THE System SHALL retain them only for the minimum required duration
4. THE System SHALL not share user data with third parties without explicit consent
5. WHEN processing Aadhaar or other sensitive documents, THE System SHALL mask sensitive fields in logs
6. THE System SHALL implement role-based access control for administrative functions

### Requirement 13: Multi-Language Support Architecture

**User Story:** As a Tamil-speaking user (நான் தமிழ் பேசுபவன்), I want the entire experience in Tamil (எனக்கு தமிழில் தகவல் வேண்டும்), so that I can use the system comfortably.

**Example:** User asks in Tamil "எனக்கு என்ன திட்டங்கள் கிடைக்கும்?" (What schemes can I get?) → System responds entirely in Tamil with scheme details, eligibility, and application steps.

#### Acceptance Criteria

1. THE System SHALL detect user language preference from initial input
2. WHEN a user switches languages mid-conversation, THE System SHALL adapt all subsequent responses
3. THE System SHALL maintain language consistency across all agents in the swarm
4. WHEN translating scheme information, THE System SHALL preserve meaning and accuracy
5. THE System SHALL support language-specific formatting conventions (dates, numbers, currency)

### Requirement 14: Error Handling and Fallback

**User Story:** As a user experiencing technical issues (सिस्टम काम नहीं कर रहा), I want clear guidance on what went wrong (मुझे बताओ क्या गलत हुआ), so that I can retry or seek alternative help.

**Example:** "आपकी आवाज़ साफ नहीं सुनाई दी। कृपया दोबारा बोलें या लिखकर भेजें।" (Your voice was not clear. Please speak again or send text message.)

#### Acceptance Criteria

1. WHEN an agent fails to process a request, THE System SHALL provide a user-friendly error message
2. WHEN AWS services are unavailable, THE System SHALL queue requests and notify users of delays
3. WHEN voice transcription fails, THE System SHALL ask the user to repeat or switch to text input
4. WHEN document OCR fails, THE System SHALL request a clearer image or manual data entry
5. IF all automated options fail, THEN THE System SHALL provide contact information for human assistance

### Requirement 15: Monitoring and Analytics

**User Story:** As a program manager, I want to track system usage and success rates, so that I can measure impact and improve the system.

#### Acceptance Criteria

1. THE System SHALL log all user interactions with timestamps and outcomes
2. THE System SHALL track metrics including query volume, scheme matches, applications started, and applications completed
3. THE System SHALL monitor agent performance including response times and error rates
4. THE System SHALL generate daily reports on system health and usage patterns
5. WHEN anomalies are detected, THE System SHALL alert administrators

### Requirement 16: Offline Capability and Resilience

**User Story:** As a user in an area with poor connectivity, I want basic functionality even with intermittent internet, so that I can still access critical information.

#### Acceptance Criteria

1. WHEN connectivity is lost during a session, THE System SHALL save conversation state
2. WHEN connectivity is restored, THE System SHALL resume from the last successful interaction
3. THE System SHALL provide cached scheme information for common queries when offline
4. WHEN operating in degraded mode, THE System SHALL clearly indicate limited functionality
5. THE System SHALL prioritize critical functions (eligibility checking, form generation) during partial outages

## Assumptions and Constraints

### Assumptions

1. Users have access to either a smartphone with WhatsApp or a nearby CSC kiosk
2. Government scheme PDFs and documentation are available in digital format
3. AWS Bedrock services are available in the India region or accessible with acceptable latency
4. Users can provide basic personal information required for eligibility checking
5. CSC operators have basic training on assisting users with the system

### Constraints

1. The system MUST use AWS Bedrock Agents as the primary orchestration mechanism
2. The system MUST use AWS Bedrock Knowledge Bases for RAG implementation
3. The system MUST use AWS Transcribe for voice-to-text conversion
4. The system MUST use AWS Polly for text-to-speech conversion
5. The system MUST use serverless architecture (Lambda, API Gateway, etc.) for deployment
6. The system MUST comply with Indian government data protection and privacy regulations
7. The system MUST support at least 10 Indian regional languages
8. The system MUST scale to support 100M+ users
9. Initial deployment must cover at least 100 government schemes
10. The system must integrate with WhatsApp Business API for messaging
