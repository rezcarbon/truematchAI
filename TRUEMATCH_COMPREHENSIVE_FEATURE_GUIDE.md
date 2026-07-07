# TrueMatch Platform - Comprehensive Feature Documentation
**For:** Slide Deck Development  
**Date:** July 6, 2026  
**Audience:** Plug & Play Inc. & Investors  
**Status:** Ready for Visual Design Integration

---

## 📱 PLATFORM OVERVIEW

### What is TrueMatch?
TrueMatch is an **AI-powered, capability-first hiring platform** that transforms recruitment by:
- Moving beyond keyword matching to **assess demonstrated capability**
- Providing **intelligent CV-to-JD matching** using Claude AI
- Implementing **governance frameworks** for fair, compliant hiring
- Enabling **multi-turn AI conversations** for deeper insights
- Supporting **three distinct user roles** with role-specific features

### The TrueMatch Difference
| Traditional ATS | TrueMatch |
|---|---|
| Keyword-based matching | Capability-based assessment |
| One-way decision making | AI-assisted, multi-turn conversations |
| Limited candidate visibility | Strength & gap identification |
| No compliance framework | Built-in governance & fairness |
| Generic experience | Role-specific AI guidance |

---

## 🎯 THE 3-PILLAR SYSTEM

### Pillar 1: AI-Powered CV Analysis
**What it does:**
- Automatically analyzes resumes using Claude AI
- Identifies key strengths and demonstrated capabilities
- Detects skills gaps and development areas
- Provides objective capability assessment
- Preserves all context (not just keywords)

**Used by:** All three roles (Admin, Recruiter, Candidate)

### Pillar 2: Intelligent JD Assessment
**What it does:**
- Analyzes job descriptions for clarity and competitiveness
- Assesses market positioning
- Identifies unrealistic or unclear requirements
- Provides improvement recommendations
- Optimizes for better candidate attraction

**Used by:** Recruiter role primarily

### Pillar 3: Capability-Based Matching
**What it does:**
- Matches candidates to positions based on capability, not just keywords
- Identifies gap areas for development
- Provides fit scoring with detailed reasoning
- Highlights "hidden gem" candidates (strong capability, keyword mismatch)
- Enables objective, data-driven hiring decisions

**Used by:** Admin & Recruiter roles

---

## 👥 ROLE-BASED FEATURES

### ROLE 1: ADMIN - Platform Oversight & Governance

**Primary Responsibilities:**
- Monitor system health and performance
- Oversee governance and compliance
- Manage users and access control
- Configure system settings
- Generate reports and analytics

#### Key Features:

**1. System Dashboard**
- Real-time system health metrics
- User activity statistics
- API performance monitoring
- Database connection status
- Chat session analytics
- Response time tracking

**2. Governance Management**
- Governance review queue (pending decisions)
- 4-Gate Framework monitoring:
  - **Coherence Gate:** Logic soundness checks
  - **Consistency Gate:** Decision alignment
  - **Fidelity Gate:** Fraud detection
  - **Bias Gate:** Fairness monitoring
- Decision approval/rejection workflow
- Audit trail logging
- Compliance reporting

**3. User Management**
- Create and manage user accounts
- Assign roles (Admin, Recruiter, Candidate)
- Control access permissions
- Monitor user activity
- View user profiles
- Manage user deactivation

**4. Analytics & Reporting**
- Hiring funnel analytics
- AI performance metrics
- Assessment decision tracking
- Governance decision history
- System usage reports
- Custom report generation

**5. Configuration**
- Governance threshold adjustment
- System preference settings
- LLM model selection
- Rate limiting configuration
- Email notification settings
- Feature flags

**6. Claude AI Chat Assistant**
- Ask about system status
- Get governance framework guidance
- Inquire about compliance requirements
- Receive system optimization recommendations
- Multi-turn conversations for complex questions
- Real Claude Opus 4.1 responses (not mocked)

#### Admin User Flow:
```
Login (admin@test.example.com) 
  → Dashboard (view metrics & alerts)
  → Chat (ask "What's our governance status?")
  → Claude response with framework guidance
  → Governance panel (review & approve decisions)
  → Adjust settings (configure thresholds)
  → Generate reports (hiring analytics)
```

---

### ROLE 2: RECRUITER - Hiring Efficiency & Candidate Evaluation

**Primary Responsibilities:**
- Post and manage job descriptions
- Evaluate candidates
- Schedule interviews
- Make hiring decisions
- Support team collaboration

#### Key Features:

**1. Job Description Management**
- Create new job postings
- Edit existing JDs
- Publish/unpublish positions
- View application statistics per role
- Manage multiple concurrent openings
- Track recruitment progress

**2. JD Optimization with Claude AI**
- Get market competitiveness analysis
- Identify clarity issues
- Receive improvement recommendations
- Multi-turn refinement conversations
- Optimize to attract better candidates
- Assess salary competitiveness

**Example JD Optimization Conversation:**
```
Recruiter: "I'm posting: Senior Full-Stack Engineer, 6+ years, 
           Python/Go, React, AWS/GCP, ML/AI, $180-220K. 
           Is this competitive?"

Claude:   "I can help you assess JD competitiveness...
          [provides detailed market analysis, positioning, and improvements]"

Recruiter: "How can we improve the requirements?"

Claude:   "[specific, actionable recommendations for better candidate fit]"
```

**3. Candidate Pipeline Management**
- View all candidates and applicants
- Organize by status (screening, interview, offer, hired, rejected)
- Add notes and tags
- Track candidate progress
- Search and filter candidates
- View candidate details

**4. CV Analysis & Screening**
- Automated CV analysis for all submissions
- Skill extraction and matching
- Capability assessment scores
- Strength and gap identification
- Candidate ranking by fit
- Export candidate data

**5. Interview Scheduling**
- Calendar integration
- Schedule different interview types:
  - Phone screens
  - Technical interviews
  - Onsite interviews
  - Panel interviews
- Send calendar invitations
- Track interview feedback
- Store interview notes

**6. Hiring Decisions**
- Record hiring decision:
  - Advance (move to next stage)
  - Hold (revisit later)
  - Interview (schedule interview)
  - Reject (end process)
  - Hire (extend offer)
- Add decision reasoning
- Generate decision communication
- Send feedback to candidate
- Create offer letters

**7. Team Collaboration**
- Share candidates with team
- Assign candidates to team members
- Leave feedback notes
- Coordinate interview scheduling
- Track team activity

**8. Claude AI Chat Assistant**
- JD optimization and review
- Candidate evaluation guidance
- Interview preparation advice
- Sourcing strategy recommendations
- Hiring best practices
- Offer negotiation tips

#### Recruiter User Flow:
```
Login (recruiter@test.example.com)
  → Dashboard (view pipeline & open positions)
  → New Job Posting (create position)
  → Chat (ask "Is this JD competitive?")
  → Get Claude optimization suggestions
  → Refine JD (multi-turn conversation)
  → Receive Applications
  → CV Analysis (automated evaluation)
  → Schedule Interviews (candidates selected)
  → Conduct Interviews
  → Make Hiring Decision (approve/reject/offer)
  → Send Decision (communicate to candidate)
```

---

### ROLE 3: CANDIDATE - Career Development & Job Search

**Primary Responsibilities:**
- Manage and optimize resume
- Search for matching positions
- Track applications
- Receive career guidance
- Develop skills

#### Key Features:

**1. Candidate Portal**
- Personal profile management
- Resume/CV management
- Notification preferences
- Account settings
- View application history
- Track interview schedule

**2. CV Management**
- Upload/update resume (PDF, DOCX)
- Store multiple CV versions
- Preview CV formatting
- Download resume
- Delete old versions
- Version history

**3. CV Optimization with Claude AI**
- Get comprehensive CV analysis
- Identify strengths
- Discover skill gaps
- Receive improvement recommendations
- Learn about market positioning
- Multi-turn refinement conversations

**Example CV Analysis Conversation:**
```
Candidate: "Can you analyze my CV? 8 years engineer, Python/React/AWS,
           led teams of 5, built ML fraud detection pipeline, scaled DBs.
           What are my strengths and gaps?"

Claude:    "[detailed CV analysis with strengths, gaps, and recommendations]"

Candidate: "How can I improve my AI/ML skills?"

Claude:    "[specific, actionable skill development path]"
```

**4. Job Search & Discovery**
- Browse available positions
- Filter by title, location, salary
- Save interesting jobs
- View job details and requirements
- See application deadline

**5. Intelligent Job Matching**
- See recommended positions based on CV
- View match percentage/score
- See fit analysis details
- Identify required vs. optional skills
- Understand capability gaps
- Find "hidden gem" opportunities (strong fit despite keywords)

**6. Application Management**
- Apply to matching positions
- Track application status
- View submission date
- See application timeline
- Receive status updates
- View recruiter feedback (if available)

**7. Interview Preparation**
- See interview schedule
- Receive interview details
- Get preparation guidance from Claude
- Practice interview questions
- Review role-specific skills
- Prepare answers

**8. Career Development Guidance**
- Skill improvement recommendations
- Portfolio building suggestions
- Interview preparation tips
- Job search strategy
- Market insights
- Career progression planning

**9. Claude AI Chat Assistant**
- CV review and improvement
- Career planning discussions
- Skill development guidance
- Job market insights
- Interview preparation help
- Salary negotiation tips
- Work-life balance advice

#### Candidate User Flow:
```
Login (candidate@test.example.com)
  → Candidate Portal (view profile & CVs)
  → Upload/Update CV
  → Chat (ask "How can I improve my CV?")
  → Get Claude analysis and recommendations
  → Job Search (browse positions)
  → View Job Match (see fit score)
  → Apply to Positions
  → Track Applications (monitor status)
  → Prepare for Interviews (get guidance)
  → Interview Participation
  → Receive Offer or Feedback
```

---

## 🤖 AI CAPABILITIES - CLAUDE OPUS 4.1

### 1. CV Analysis
**What Claude analyzes:**
- Work experience quality and progression
- Demonstrated skills vs. claimed skills
- Leadership and impact
- Technical depth vs. breadth
- Problem-solving approach
- Communication clarity
- Market competitiveness
- Growth trajectory

**Output includes:**
- Strengths (concrete evidence)
- Development areas (specific gaps)
- Market positioning
- Recommended improvements
- Comparable roles suitability

### 2. JD Assessment
**What Claude evaluates:**
- Requirement clarity and specificity
- Experience level realistic for compensation
- Market competitiveness
- Requirement creep (asking for too much)
- Role clarity for candidates
- Potential bias in language
- Skill priority (essential vs. nice-to-have)
- Salary alignment with market

**Output includes:**
- Competitiveness score
- Market positioning
- Clarity assessment
- Specific improvement recommendations
- Potential risk areas

### 3. CV-to-JD Matching
**What Claude calculates:**
- Direct skill matches
- Adjacent skill application
- Capability transfer potential
- Growth opportunity fit
- Culture/value alignment
- Development gaps
- Time to productivity

**Output includes:**
- Match percentage (0-100%)
- Strength alignment details
- Gap analysis
- Onboarding priorities
- Development plan

### 4. Governance & Compliance
**What Claude advises:**
- Fair hiring practices
- Bias prevention
- Compliance requirements
- Legal considerations
- Documentation requirements
- Decision rationale

**Output includes:**
- Framework recommendations
- Best practices
- Risk mitigation strategies
- Compliance checklist

### 5. Multi-turn Conversations
**What makes Claude unique:**
- Remembers previous context
- Refines answers based on follow-ups
- Explores deeper insights
- Answers clarifying questions
- Adjusts recommendations
- Provides increasingly specific guidance

**Example flow:**
```
Turn 1: "Is this JD competitive?"
Claude: [general competitiveness analysis]

Turn 2: "How do we attract senior developers?"
Claude: [builds on previous JD, adds sourcing strategy]

Turn 3: "What about remote work options?"
Claude: [incorporates flexibility into recommendations]
```

---

## 🔄 KEY WORKFLOWS

### WORKFLOW A: Complete Hiring Cycle

#### Phase 1: Preparation (Recruiter + Claude)
1. **Draft JD**
   - Recruiter creates job description
   - Adds position details, requirements, compensation

2. **Optimize with Claude**
   - Chat: "Review this JD for competitiveness"
   - Claude provides market analysis
   - Recruiter refines requirements
   - Multi-turn refinement conversations

3. **Publish Position**
   - Finalize JD
   - Post to job board
   - Notify hiring team

#### Phase 2: Screening (Admin + Recruiter + Claude)
1. **Receive Applications**
   - Candidates submit resumes
   - Applications arrive in pipeline

2. **Automated CV Analysis**
   - Claude analyzes each CV
   - Extracts key capabilities
   - Identifies strengths and gaps
   - Generates candidate scores

3. **Shortlist Candidates**
   - View analysis results
   - Chat with Claude: "Which candidates are strongest fits?"
   - Recruiter selects interview candidates

#### Phase 3: Interview (Recruiter + Candidate)
1. **Schedule Interviews**
   - Recruiter schedules with candidates
   - Calendar invitations sent
   - Interview details provided

2. **Prepare (Candidate + Claude)**
   - Candidate asks: "How should I prepare?"
   - Claude provides interview guidance
   - Practice suggestions

3. **Conduct Interviews**
   - Interview takes place
   - Feedback recorded

#### Phase 4: Decision (Recruiter + Admin)
1. **Make Decision**
   - Recruiter reviews candidate profile
   - Considers interview feedback
   - Reviews Claude's analysis
   - Makes hiring decision

2. **Governance Review (if needed)**
   - Admin reviews high-impact decisions
   - Verifies compliance
   - Approves or challenges decision

3. **Communicate**
   - Send offer or rejection
   - Provide feedback

---

### WORKFLOW B: Candidate Career Development

#### Phase 1: Assessment
1. **Upload CV**
   - Candidate uploads resume
   - Multiple versions allowed

2. **Get Analysis**
   - Chat: "Analyze my CV and suggest improvements"
   - Claude provides detailed feedback
   - Identifies strengths and development areas

#### Phase 2: Improvement
1. **Plan Development**
   - Chat: "What skills should I focus on?"
   - Claude recommends priority skills
   - Suggests learning path

2. **Update CV**
   - Add new projects/skills
   - Highlight relevant experiences
   - Reupload updated resume

3. **Verify Improvement**
   - Chat: "How much does this improve my profile?"
   - Claude compares old and new CV
   - Identifies remaining gaps

#### Phase 3: Job Search
1. **Discover Opportunities**
   - Browse open positions
   - Review match scores
   - Understand fit analysis

2. **Apply Strategically**
   - Apply to high-match roles
   - Customize application (if applicable)
   - Prepare customized cover letter

3. **Interview Preparation**
   - Chat: "Help me prepare for interviews"
   - Claude provides interview tips
   - Role-specific guidance

#### Phase 4: Success
1. **Participate in Interviews**
   - Leverage preparation
   - Demonstrate capability

2. **Receive Offer**
   - Negotiate offer (Claude guidance available)
   - Accept role
   - Begin onboarding

---

## 🎨 USER INTERFACE HIGHLIGHTS

### Core Pages & Screens

#### Authentication
- **Login Page:** Clean, simple login with email/password
- **Signup Page:** Role selection and account creation
- **Password Recovery:** Secure password reset flow

#### Dashboards (Role-Specific)
- **Admin Dashboard:** Metrics cards, governance alerts, system status
- **Recruiter Dashboard:** Pipeline overview, open positions, recent activity
- **Candidate Dashboard:** Profile status, saved jobs, application tracking

#### Chat Interface
- **Chat Sidebar:** List of chat sessions
- **Message Display:** User and assistant messages in conversation format
- **Input Box:** Message composition and send button
- **Response Formatting:** Claude responses with markdown, code blocks, formatting

#### Feature Pages
- **Admin Features:** Settings, governance panel, user management, analytics
- **Recruiter Features:** Job management, candidate pipeline, interview scheduler
- **Candidate Features:** CV management, job search, application tracking

#### Key Interactions
- **CV Upload:** Drag-and-drop or file selection
- **Chat Input:** Multi-line text input with formatting
- **Decision Forms:** Structured forms for recording decisions
- **Date/Time Pickers:** Calendar for scheduling interviews
- **Status Badges:** Visual indicators for application/job status

---

## 📱 MOBILE & iOS APP

### iOS App Structure (Awaiting Detailed Exploration)
- **Authentication:** Secure login/signup
- **Dashboard:** Mobile-optimized home screen
- **Chat:** Full conversation interface
- **Profile:** User profile management
- **Search/Browse:** Job and candidate discovery
- **Notifications:** Push notifications for updates

### iOS-Specific Features
- **Offline Support:** Access cached information
- **Push Notifications:** Interview reminders, application updates
- **Biometric Auth:** Face ID / Touch ID login
- **Mobile-Optimized Chat:** Conversational UI optimized for phones
- **Quick Actions:** Shortcuts for common tasks

---

## 🔧 TECHNICAL ARCHITECTURE

### Technology Stack
- **Backend:** FastAPI (Python) with async/await
- **Frontend:** Next.js 14 (React) with TypeScript
- **Mobile:** Swift (iOS) with SwiftUI
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Caching:** Redis for session/performance
- **AI:** Anthropic Claude Opus 4.1 API
- **Authentication:** JWT tokens with NextAuth
- **Hosting:** Cloud-ready (AWS/GCP compatible)

### Key Architectural Decisions
1. **BFF Pattern:** Backend-for-Frontend proxy for secure token injection
2. **Async Processing:** Non-blocking chat handling with Claude
3. **Session Memory:** Conversation context persisted across turns
4. **Circuit Breaker:** Protection against API failures
5. **Role-Based Access:** Enforced at database and API level

---

## 📊 FEATURE SUMMARY TABLE

| Feature | Admin | Recruiter | Candidate | Mobile |
|---------|-------|-----------|-----------|--------|
| **Authentication** | ✅ | ✅ | ✅ | ✅ |
| **Dashboard** | ✅ | ✅ | ✅ | ✅ |
| **Chat Interface** | ✅ | ✅ | ✅ | ✅ |
| **System Monitoring** | ✅ | — | — | — |
| **Governance Review** | ✅ | — | — | — |
| **User Management** | ✅ | — | — | — |
| **JD Management** | — | ✅ | — | ✅ |
| **JD Optimization** | — | ✅ | — | ✅ |
| **Job Posting** | — | ✅ | — | ✅ |
| **Candidate Pipeline** | — | ✅ | — | ✅ |
| **CV Analysis** | ✅ | ✅ | ✅ | ✅ |
| **Interview Scheduling** | — | ✅ | ✅ | ✅ |
| **Job Search** | — | — | ✅ | ✅ |
| **CV-to-JD Matching** | ✅ | ✅ | ✅ | ✅ |
| **Hiring Decisions** | — | ✅ | — | ✅ |
| **Reports** | ✅ | ✅ | ✅ | — |
| **Claude AI Chat** | ✅ | ✅ | ✅ | ✅ |

---

## 🎯 VALUE PROPOSITIONS BY ROLE

### For Admins
- **Control & Oversight:** Complete visibility into hiring process
- **Governance:** Built-in fairness and compliance
- **Analytics:** Data-driven insights
- **Configuration:** Customize to organizational needs

### For Recruiters
- **Efficiency:** Automated CV analysis saves time
- **Quality:** Capability-based matching finds better candidates
- **Intelligence:** Claude guidance improves JD and strategy
- **Collaboration:** Team features streamline coordination

### For Candidates
- **Development:** Personalized career guidance
- **Optimization:** Improve CV for better matches
- **Discovery:** Find truly matching opportunities
- **Preparation:** Interview readiness support

---

## ✨ DIFFERENTIATORS

1. **Real Claude AI** - Not mocked, actual production API
2. **Capability-First** - Moves beyond keyword matching
3. **Multi-turn Intelligence** - Conversations, not one-off responses
4. **Governance Built-in** - Compliance from day one
5. **Three Complete Personas** - Distinct experiences for each role
6. **Production-Ready** - Scalable, secure, performant
7. **Cross-Platform** - Web, desktop, and iOS
8. **Enterprise Features** - Role-based access, audit trails, reporting

---

## 🚀 SLIDE DECK NEXT STEPS

1. ✅ Feature documentation (THIS DOCUMENT)
2. ⏳ iOS app feature details (from codebase exploration)
3. 📸 Screenshot collection (manual or automated)
4. 🎨 Visual design and layout
5. 📝 Narrative and talking points
6. ✅ Feature matrices and comparison tables
7. 📊 Performance and capability metrics
8. 🎬 Final presentation review

---

**Status:** Ready for visual design integration  
**Next Step:** Await iOS app exploration results and begin slide creation

