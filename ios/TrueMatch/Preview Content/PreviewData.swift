//
//  PreviewData.swift
//  TrueMatch
//
//  Realistic sample data for SwiftUI previews and offline UI development.
//  Not compiled into release builds beyond preview usage.
//

import Foundation

enum PreviewData {

    // MARK: - Sample Assessment (completed, counter-recommended)

    static let sampleAssessment = AssessmentResponse(
        id: "asmt_8f31c2",
        status: .completed,
        traditionalScore: TraditionalScore(
            score: 42,
            matchedKeywords: ["Python", "REST APIs", "Agile", "PostgreSQL"],
            missingKeywords: ["Kubernetes", "Terraform", "Go", "5+ years"],
            explanation: "Resume matches 4 of 8 required keywords. Title and tenure do not literally match the seniority band requested."
        ),
        capabilityScore: CapabilityScore(
            score: 87,
            components: CapabilityComponents(
                demonstratedCapability: 0.91,
                domainDepth: 0.78,
                trajectoryStrength: 0.88,
                learningVelocity: 0.93,
                leadershipEvidence: 0.71
            ),
            narrative: "This candidate consistently operates well above their formal title. They have repeatedly taken ownership of ambiguous, high-impact infrastructure work — shipping a platform migration and an incident-response overhaul without holding a senior or staff designation. Their learning velocity is exceptional: each role shows a step-change in scope acquired in under two quarters.",
            evidence: [
                "Led a 6-engineer database migration with zero downtime",
                "Built the on-call runbook now used company-wide",
                "Self-taught distributed systems on the job, later mentoring two peers",
                "Promoted twice in 30 months"
            ]
        ),
        delta: 45,
        counterRecommendation: CounterRecommendation(
            triggered: true,
            reasoning: "The traditional keyword filter would reject this candidate for missing 'Kubernetes' and the '5+ years' band. However, demonstrated capability and trajectory strongly indicate they can perform at the target level. Recommend advancing to interview.",
            evidencePoints: [
                "Trajectory velocity in the top decile of the applicant pool",
                "Demonstrated capability score of 0.91 on owned initiatives",
                "Missing keywords are tools learnable within onboarding"
            ]
        ),
        jdQuality: JDQuality(
            score: 61,
            issues: [
                "Hard '5+ years' gate excludes high-trajectory candidates",
                "Lists 11 'required' skills — likely over-specified",
                "No distinction between must-have and nice-to-have"
            ],
            recommendations: [
                "Reframe years-of-experience as a capability band",
                "Split required vs. preferred skills",
                "Add an evidence-based screening question"
            ]
        ),
        trajectory: Trajectory(
            direction: "accelerating",
            velocity: 0.88,
            domainCrossings: 2,
            narrative: "Moved from front-end to platform to infrastructure, each time expanding scope faster than peers. The pattern indicates a generalist who compounds skills rather than plateauing.",
            invisibleCredentials: [
                "Cross-domain fluency not captured by any single job title",
                "Demonstrated ownership ahead of formal authority",
                "Mentorship impact on team retention"
            ]
        ),
        governance: Governance(
            coherence: GovernanceMetric(status: "pass", score: 0.94),
            consistency: GovernanceConsistency(status: "pass", delta: 0.02),
            fidelity: GovernanceMetric(status: "watch", score: 0.81),
            biasFlags: [],
            auditId: "audit_2026_05_31_a1b2c3"
        ),
        createdAt: Date(timeIntervalSinceNow: -3600)
    )

    // MARK: - Sample Assessment (processing)

    static let processingAssessment = AssessmentResponse(
        id: "asmt_inflight",
        status: .processing,
        traditionalScore: nil,
        capabilityScore: nil,
        delta: nil,
        counterRecommendation: nil,
        jdQuality: nil,
        trajectory: nil,
        governance: nil,
        createdAt: Date()
    )

    // MARK: - Sample List

    static let assessmentList: [AssessmentResponse] = [
        sampleAssessment,
        AssessmentResponse(
            id: "asmt_771a",
            status: .completed,
            traditionalScore: TraditionalScore(score: 78, matchedKeywords: ["Swift", "iOS"], missingKeywords: ["SwiftData"], explanation: "Strong keyword match."),
            capabilityScore: CapabilityScore(score: 64, components: CapabilityComponents(demonstratedCapability: 0.6, domainDepth: 0.8, trajectoryStrength: 0.55, learningVelocity: 0.5, leadershipEvidence: 0.4), narrative: "Solid, steady contributor with deep but narrow domain experience.", evidence: ["8 years in one domain"]),
            delta: -14,
            counterRecommendation: CounterRecommendation(triggered: false, reasoning: nil, evidencePoints: []),
            jdQuality: JDQuality(score: 84, issues: [], recommendations: []),
            trajectory: Trajectory(direction: "steady", velocity: 0.5, domainCrossings: 0, narrative: "Consistent single-domain depth.", invisibleCredentials: []),
            governance: Governance(coherence: GovernanceMetric(status: "pass", score: 0.9), consistency: GovernanceConsistency(status: "pass", delta: 0.01), fidelity: GovernanceMetric(status: "pass", score: 0.92), biasFlags: [], auditId: "audit_771a"),
            createdAt: Date(timeIntervalSinceNow: -86_400)
        )
    ]

    // MARK: - Sample Position

    static let samplePosition = PositionResponse(
        id: "pos_91",
        title: "Senior Backend Engineer",
        department: "Platform",
        jobDescription: "We are looking for a senior backend engineer with 5+ years of experience in Python, Kubernetes, Terraform...",
        createdAt: Date(timeIntervalSinceNow: -172_800)
    )

    // MARK: - Sample Profile

    static let sampleProfile = UserProfileResponse(
        userId: "user_42",
        displayName: "Alex Tan",
        email: "alex.tan@example.com",
        maskedNric: "S••••567A"
    )
}
