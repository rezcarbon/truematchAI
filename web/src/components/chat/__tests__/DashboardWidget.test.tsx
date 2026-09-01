import { render, screen, fireEvent } from "@testing-library/react";
import { DashboardWidget } from "../DashboardWidget";

describe("DashboardWidget", () => {
  it("renders cards with label, value and delta", () => {
    render(
      <DashboardWidget
        data={{
          title: "System Status",
          cards: [
            { label: "Active Assessments", value: "42", delta: "+12%", intent: "up", hint: "vs last week" },
            { label: "Pending Reviews", value: 3, intent: "warn" },
          ],
        }}
      />
    );
    expect(screen.getByText("System Status")).toBeInTheDocument();
    expect(screen.getByText("Active Assessments")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("+12%")).toBeInTheDocument();
    expect(screen.getByText("vs last week")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders a prompt card as a button and fires onPrompt on click", () => {
    const onPrompt = jest.fn();
    render(
      <DashboardWidget
        data={{ cards: [{ label: "Pipeline", value: "8", prompt: "Show the pipeline" }] }}
        onPrompt={onPrompt}
      />
    );
    fireEvent.click(screen.getByText("Pipeline"));
    expect(onPrompt).toHaveBeenCalledWith("Show the pipeline");
  });

  it("renders an href card as a link", () => {
    render(
      <DashboardWidget
        data={{ cards: [{ label: "Analytics", value: "↗", href: "/admin/analytics" }] }}
      />
    );
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/admin/analytics");
  });

  it("renders nothing when there are no cards", () => {
    const { container } = render(<DashboardWidget data={{ cards: [] }} />);
    expect(container).toBeEmptyDOMElement();
  });
});
