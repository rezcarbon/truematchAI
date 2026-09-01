//
//  ThreeSignalGapView.swift
//  TrueMatch
//
//  The signature capability-gap visual, mirroring the web CapabilityGap
//  component: the gap between what an ATS sees (keyword) and real fit, the
//  before→after legibility lift, and (when supplied) the capability verdict as
//  a constant anchor. Used in the Capability Translation results.
//

import SwiftUI

struct ThreeSignalGapView: View {
    @Environment(\.trueMatchTheme) private var theme
    let beforeKeyword: Int
    let afterKeyword: Int
    let beforeSemantic: Int
    let afterSemantic: Int
    var capability: Int? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            gapRow("Auto-screen match", sub: "what the hiring software reads",
                   before: beforeKeyword, after: afterKeyword, anchor: false)
            gapRow("Experience overlap", sub: "how well your background maps to the role",
                   before: beforeSemantic, after: afterSemantic, anchor: false)
            if let cap = capability {
                gapRow("Capability verdict", sub: "our considered judgment of your real fit",
                       before: nil, after: cap, anchor: true)
                let delta = cap - beforeKeyword
                Text("Hidden-gem signal: +\(delta). Your capability (\(cap)) far exceeds what the auto-screen credits (\(beforeKeyword)).")
                    .font(.caption)
                    .foregroundStyle(theme.colors.capability)
            }
        }
    }

    @ViewBuilder
    private func gapRow(_ label: String, sub: String, before: Int?, after: Int, anchor: Bool) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 1) {
                    Text(label).font(.subheadline.weight(.semibold))
                    Text(sub).font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                if anchor {
                    Text("\(after) / 100").font(.callout.weight(.bold)).foregroundStyle(theme.colors.capability)
                } else if let b = before {
                    HStack(spacing: 4) {
                        Text("\(b)").foregroundStyle(.secondary)
                        Image(systemName: "arrow.right").font(.caption2).foregroundStyle(.secondary)
                        Text("\(after)").font(.callout.weight(.bold))
                    }
                }
            }
            GeometryReader { geo in
                let w = geo.size.width
                let clamp: (Int) -> CGFloat = { CGFloat(min(max($0, 0), 100)) / 100.0 }
                ZStack(alignment: .leading) {
                    Capsule().fill(Color.secondary.opacity(0.15)).frame(height: 7)
                    Capsule().fill(theme.colors.capability).frame(width: w * clamp(after), height: 7)
                    if !anchor, let b = before {
                        Rectangle().fill(Color.primary.opacity(0.4))
                            .frame(width: 2, height: 13)
                            .offset(x: w * clamp(b) - 1)
                    }
                }
            }
            .frame(height: 13)
        }
    }
}
