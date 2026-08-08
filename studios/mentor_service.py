"""AI Mentors — role-based conversational AI assistants.

Mentors:
  - data_mentor: Teaches beginners analytics
  - research_assistant: Helps researchers
  - business_consultant: Turns analysis into decisions
  - statistical_advisor: Suggests correct statistical methods
  - dashboard_designer: Creates dashboards automatically
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from studios.models import AIMentorSession

MENTOR_PROFILES = {
    "data_mentor": {
        "name": "Data Mentor",
        "description": "Teaches beginners how to understand and analyze data",
        "system_prompt": (
            "You are an AI Data Mentor. Your role is to teach beginners data analytics "
            "in a simple, encouraging way. Explain concepts using everyday language. "
            "Use analogies. Break down complex topics into steps. "
            "Always provide examples and practice suggestions."
        ),
        "capabilities": [
            "Explain basic statistics (mean, median, mode) with examples",
            "Guide users through their first data analysis",
            "Suggest beginner-friendly visualizations",
            "Explain what charts mean in plain language",
            "Teach data cleaning concepts step by step",
        ],
        "suggested_questions": [
            "What does average mean?",
            "How do I read a bar chart?",
            "What is the difference between mean and median?",
            "How do I find outliers in my data?",
            "What chart should I use for my data?",
        ],
    },
    "research_assistant": {
        "name": "Research Assistant",
        "description": "Helps researchers design studies and analyze data",
        "system_prompt": (
            "You are an AI Research Assistant. You help researchers design studies, "
            "formulate hypotheses, choose statistical tests, and interpret results. "
            "Always cite the assumptions and limitations of recommended methods. "
            "Suggest appropriate sample sizes and research designs."
        ),
        "capabilities": [
            "Suggest research designs based on questions",
            "Generate hypotheses from research questions",
            "Recommend appropriate statistical tests",
            "Help interpret p-values and effect sizes",
            "Draft methodology sections",
        ],
        "suggested_questions": [
            "What statistical test should I use?",
            "How do I calculate sample size?",
            "What is the difference between ANOVA and t-test?",
            "How do I interpret a p-value of 0.03?",
            "What research design fits my question?",
        ],
    },
    "business_consultant": {
        "name": "Business Consultant",
        "description": "Turns data analysis into business decisions",
        "system_prompt": (
            "You are an AI Business Consultant. You translate data findings into "
            "actionable business recommendations. Focus on ROI, risk, and strategic impact. "
            "Always provide clear next steps and expected outcomes."
        ),
        "capabilities": [
            "Interpret business metrics and KPIs",
            "Recommend actions based on data trends",
            "Assess business risks from data patterns",
            "Prioritize opportunities by impact",
            "Generate executive summaries from analyses",
        ],
        "suggested_questions": [
            "Why did sales drop last quarter?",
            "What should I focus on to improve revenue?",
            "Which products should I discontinue?",
            "What are the biggest risks in my data?",
            "How can I reduce customer churn?",
        ],
    },
    "statistical_advisor": {
        "name": "Statistical Advisor",
        "description": "Suggests the correct statistical methods for any scenario",
        "system_prompt": (
            "You are an AI Statistical Advisor. You recommend the correct statistical "
            "tests based on data types, research questions, and assumptions. "
            "Always check and report assumptions. Explain when non-parametric alternatives are needed."
        ),
        "capabilities": [
            "Recommend tests based on data types and research design",
            "Check statistical assumptions (normality, homogeneity, independence)",
            "Suggest non-parametric alternatives",
            "Explain effect sizes and power analysis",
            "Interpret confidence intervals and significance",
        ],
        "suggested_questions": [
            "Which test compares two groups?",
            "How do I check if my data is normal?",
            "What is a non-parametric alternative to ANOVA?",
            "How do I interpret a confidence interval?",
            "What sample size do I need for 80% power?",
        ],
    },
    "dashboard_designer": {
        "name": "Dashboard Designer",
        "description": "Creates dashboards automatically from your data",
        "system_prompt": (
            "You are an AI Dashboard Designer. You create effective, visually appealing "
            "dashboards from datasets. You choose the right charts, arrange them logically, "
            "and ensure the dashboard tells a clear story. Follow data visualization best practices."
        ),
        "capabilities": [
            "Auto-select charts based on data characteristics",
            "Design dashboard layouts for different audiences",
            "Choose color schemes and visual styles",
            "Suggest KPIs and summary metrics",
            "Create interactive filter configurations",
        ],
        "suggested_questions": [
            "Create a dashboard for my sales data",
            "What KPIs should I track for healthcare?",
            "Design an executive summary dashboard",
            "How should I arrange my charts?",
            "What colors work best for dashboards?",
        ],
    },
}


class AIMentorService:
    """Service for AI mentor conversations."""

    def __init__(self, db: DbSession):
        self.db = db

    def list_mentors(self) -> list[dict]:
        """List all available AI mentors."""
        return [
            {
                "mentor_type": key,
                "name": profile["name"],
                "description": profile["description"],
                "capabilities": profile["capabilities"],
                "suggested_questions": profile["suggested_questions"],
            }
            for key, profile in MENTOR_PROFILES.items()
        ]

    def get_mentor_profile(self, mentor_type: str) -> dict | None:
        return MENTOR_PROFILES.get(mentor_type)

    def create_session(
        self,
        org_id: int,
        user_id: int,
        mentor_type: str,
        title: str | None = None,
        context: dict | None = None,
    ) -> AIMentorSession:
        if mentor_type not in MENTOR_PROFILES:
            raise ValueError(f"Unknown mentor type: {mentor_type}")

        profile = MENTOR_PROFILES[mentor_type]
        session = AIMentorSession(
            organization_id=org_id,
            user_id=user_id,
            mentor_type=mentor_type,
            title=title or profile["name"],
            messages=[
                {
                    "role": "assistant",
                    "content": f"Hello! I'm your {profile['name']}. {profile['description']}. How can I help you today?",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ],
            context=context,
        )
        self.db.add(session)
        self.db.commit()
        return session

    def list_sessions(self, org_id: int, user_id: int) -> list[AIMentorSession]:
        return (
            self.db.execute(
                select(AIMentorSession)
                .where(
                    AIMentorSession.organization_id == org_id,
                    AIMentorSession.user_id == user_id,
                    AIMentorSession.is_active == True,  # noqa: E712
                )
                .order_by(AIMentorSession.updated_at.desc())
            )
            .scalars()
            .all()
        )

    def get_session(self, session_id: int, org_id: int) -> AIMentorSession | None:
        return self.db.execute(
            select(AIMentorSession).where(
                AIMentorSession.id == session_id,
                AIMentorSession.organization_id == org_id,
            )
        ).scalar_one_or_none()

    def add_message(
        self, session_id: int, role: str, content: str, metadata: dict | None = None
    ) -> dict:
        """Add a message to a mentor session and generate a response."""
        session = self.db.execute(
            select(AIMentorSession).where(AIMentorSession.id == session_id)
        ).scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        messages = session.messages or []
        messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
            }
        )

        # Generate response based on mentor type
        if role == "user":
            response = self._generate_response(session.mentor_type, content, session.context)
            messages.append(
                {
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        else:
            response = content

        session.messages = messages
        self.db.commit()
        return {"response": response, "messages": messages}

    @staticmethod
    def _generate_response(mentor_type: str, user_message: str, context: dict | None = None) -> str:
        """Generate a context-aware response from the AI mentor.

        This is a rule-based response system. In production, this would call an LLM
        with the mentor's system prompt and conversation context.
        """
        msg = user_message.lower()
        MENTOR_PROFILES.get(mentor_type, {})

        # Data Mentor responses
        if mentor_type == "data_mentor":
            if "mean" in msg or "average" in msg:
                return (
                    "Great question! The **mean** (or average) is like sharing equally. "
                    "If you have 10, 20, and 30, the mean is (10+20+30)÷3 = 20. "
                    "Everyone gets 20. It's the most common way to describe 'typical' values. "
                    "\n\n**Tip:** The mean can be affected by very large or very small numbers (outliers). "
                    "That's why we also have the **median** (the middle value when sorted). "
                    "Would you like to learn about median too?"
                )
            elif "median" in msg:
                return (
                    "The **median** is the middle value when you sort your data. "
                    "For [5, 10, 15, 20, 100], the median is 15 (the middle one). "
                    "It's great when you have extreme values because it's not pulled by them. "
                    "\n\n**Example:** If 9 people earn $1,000 and 1 person earns $1,000,000, "
                    "the mean is $100,900 but the median is $1,000. The median better represents 'typical' pay."
                )
            elif "chart" in msg or "graph" in msg or "visual" in msg:
                return (
                    "Choosing the right chart makes data easy to understand:\n\n"
                    "- **Bar chart:** Compare categories (e.g., sales by region)\n"
                    "- **Line chart:** Show trends over time (e.g., monthly revenue)\n"
                    "- **Pie chart:** Show proportions (e.g., market share)\n"
                    "- **Scatter plot:** Show relationships (e.g., price vs. demand)\n\n"
                    "What data do you have? I can suggest the best chart for it!"
                )
            elif "outlier" in msg:
                return (
                    "An **outlier** is a value that's very different from the rest — like a 6-foot person "
                    "in a group of 5-foot people. They can distort your analysis.\n\n"
                    "To find them:\n"
                    "1. Sort your data\n"
                    "2. Look for values that are much higher or lower than most\n"
                    "3. Use the IQR method: values below Q1-1.5×IQR or above Q3+1.5×IQR are outliers\n\n"
                    "Would you like me to help you identify outliers in your dataset?"
                )
            return (
                "I'm here to help you understand data! I can explain:\n\n"
                "- Basic statistics (mean, median, mode, standard deviation)\n"
                "- How to choose the right chart\n"
                "- What outliers are and how to find them\n"
                "- How to clean your data\n"
                "- How to read and interpret graphs\n\n"
                "What would you like to learn about?"
            )

        # Research Assistant responses
        elif mentor_type == "research_assistant":
            if "test" in msg or "method" in msg or "statistical" in msg:
                return (
                    "To recommend the right statistical test, I need to know:\n\n"
                    "1. **Your research question** (comparison, relationship, prediction?)\n"
                    "2. **Data types** (categorical, continuous, ordinal?)\n"
                    "3. **Number of groups** (2 groups, 3+ groups?)\n"
                    "4. **Sample size**\n\n"
                    "Quick guide:\n"
                    "- 2 groups, continuous → **t-test** (or Mann-Whitney U if non-normal)\n"
                    "- 3+ groups, continuous → **ANOVA** (or Kruskal-Wallis)\n"
                    "- 2 categorical variables → **Chi-square test**\n"
                    "- 2 continuous variables → **Correlation** (Pearson or Spearman)\n"
                    "- Predict a continuous outcome → **Regression**\n\n"
                    "What's your research question?"
                )
            elif "hypothesis" in msg:
                return (
                    "A good hypothesis should be:\n"
                    "- **Specific:** Clearly state the expected relationship\n"
                    "- **Testable:** Can be verified with data\n"
                    "- **Falsifiable:** Can be proven wrong\n\n"
                    "Example:\n"
                    "- H1: There is a significant difference in test scores between students "
                    "who use digital tools and those who don't.\n"
                    "- H0 (null): There is no significant difference.\n\n"
                    "What's your research question? I can help formulate hypotheses."
                )
            elif "sample size" in msg or "power" in msg:
                return (
                    "Sample size depends on:\n"
                    "1. **Effect size** (how big a difference you expect)\n"
                    "2. **Significance level** (α, usually 0.05)\n"
                    "3. **Power** (usually 0.80 or 80%)\n"
                    "4. **Number of groups/predictors**\n\n"
                    "Rule of thumb:\n"
                    "- t-test: ≥30 per group\n"
                    "- ANOVA: ≥30 per group\n"
                    "- Regression: ≥10 observations per predictor\n\n"
                    "For precise calculation, use a power analysis tool."
                )
            return (
                "I'm your Research Assistant! I can help with:\n\n"
                "- Designing your research study\n"
                "- Formulating hypotheses\n"
                "- Choosing statistical tests\n"
                "- Interpreting results\n"
                "- Writing methodology sections\n\n"
                "What stage of research are you at?"
            )

        # Business Consultant responses
        elif mentor_type == "business_consultant":
            if "sales" in msg and ("drop" in msg or "decline" in msg or "decrease" in msg):
                return (
                    "To diagnose a sales drop, I recommend analyzing:\n\n"
                    "1. **Time pattern:** Was it sudden or gradual?\n"
                    "2. **Segment breakdown:** Which products, regions, or channels are affected?\n"
                    "3. **External factors:** Seasonality, competitor actions, economic changes?\n"
                    "4. **Internal factors:** Pricing, marketing spend, product availability?\n\n"
                    "**Immediate action:**\n"
                    "- Compare this period vs. same period last year\n"
                    "- Identify which segment contributed most to the decline\n"
                    "- Check if it's a volume issue (fewer customers) or a value issue (lower prices/basket size)\n\n"
                    "Would you like me to analyze your sales data?"
                )
            elif "churn" in msg or "retention" in msg:
                return (
                    "Customer churn analysis requires:\n\n"
                    "1. **Define churn:** When is a customer considered 'lost'?\n"
                    "2. **Identify patterns:** What do churning customers have in common?\n"
                    "3. **Build a prediction model:** Who's likely to churn next?\n"
                    "4. **Take action:** Target at-risk customers with retention campaigns\n\n"
                    "**Key metrics:**\n"
                    "- Churn rate = lost customers / total customers\n"
                    "- Retention rate = 1 - churn rate\n"
                    "- Customer lifetime value (CLV)\n\n"
                    "I can help you build a churn prediction model from your data."
                )
            return (
                "I'm your Business Consultant! I can help you:\n\n"
                "- Diagnose business problems from data\n"
                "- Identify growth opportunities\n"
                "- Prioritize actions by ROI\n"
                "- Assess risks and opportunities\n"
                "- Generate executive recommendations\n\n"
                "What business challenge are you facing?"
            )

        # Statistical Advisor responses
        elif mentor_type == "statistical_advisor":
            if "normal" in msg:
                return (
                    "To check normality:\n\n"
                    "**Visual methods:**\n"
                    "- Histogram: Should look bell-shaped\n"
                    "- Q-Q plot: Points should follow the diagonal line\n\n"
                    "**Statistical tests:**\n"
                    "- Shapiro-Wilk (n < 5000): Best for small samples\n"
                    "- Kolmogorov-Smirnov: For larger samples\n"
                    "- Anderson-Darling: More sensitive to tails\n\n"
                    "**Interpretation:**\n"
                    "- p > 0.05 → Data is likely normal\n"
                    "- p < 0.05 → Data is likely not normal → use non-parametric tests\n\n"
                    "Would you like me to run a normality test on your data?"
                )
            elif "non-parametric" in msg or "nonparametric" in msg:
                return (
                    "Non-parametric tests don't assume normal distribution:\n\n"
                    "| Parametric | Non-parametric alternative |\n"
                    "|-----------|--------------------------|\n"
                    "| Independent t-test | Mann-Whitney U |\n"
                    "| Paired t-test | Wilcoxon signed-rank |\n"
                    "| One-way ANOVA | Kruskal-Wallis |\n"
                    "| Pearson correlation | Spearman correlation |\n\n"
                    "Use non-parametric tests when:\n"
                    "- Data is not normally distributed\n"
                    "- Sample size is small (n < 30)\n"
                    "- Data is ordinal or ranked"
                )
            elif "effect size" in msg:
                return (
                    "Effect size tells you how **meaningful** a difference is, not just if it's statistically significant.\n\n"
                    "**Common effect sizes:**\n"
                    "- Cohen's d (t-test): 0.2=small, 0.5=medium, 0.8=large\n"
                    "- η² (ANOVA): 0.01=small, 0.06=medium, 0.14=large\n"
                    "- r (correlation): 0.1=small, 0.3=medium, 0.5=large\n\n"
                    "**Why it matters:**\n"
                    "A large sample can find a 'significant' result that's trivially small. "
                    "Effect size tells you if the finding actually matters in practice."
                )
            return (
                "I'm your Statistical Advisor! I can help with:\n\n"
                "- Choosing the right statistical test\n"
                "- Checking assumptions (normality, homogeneity, independence)\n"
                "- Non-parametric alternatives\n"
                "- Effect sizes and power analysis\n"
                "- Interpreting confidence intervals and p-values\n\n"
                "What statistical question do you have?"
            )

        # Dashboard Designer responses
        elif mentor_type == "dashboard_designer":
            if "create" in msg or "design" in msg or "build" in msg:
                return (
                    "I'll design a dashboard for you! I need to know:\n\n"
                    "1. **Who's the audience?** (executives, analysts, operators?)\n"
                    "2. **What data do you have?** (sales, operations, healthcare?)\n"
                    "3. **What decisions will it support?**\n\n"
                    "**Dashboard design principles:**\n"
                    "- Top-left: Most important KPIs\n"
                    "- Top-right: Trends over time\n"
                    "- Bottom: Detailed breakdowns\n"
                    "- Use 5-7 charts maximum\n"
                    "- Consistent color scheme\n"
                    "- Clear titles and labels\n\n"
                    "What data would you like on your dashboard?"
                )
            elif "kpi" in msg:
                return (
                    "KPIs depend on your industry and goals:\n\n"
                    "- **Healthcare:** Patient satisfaction, readmission rate, bed occupancy\n"
                    "- **Education:** Student performance, graduation rate, attendance\n"
                    "- **Banking:** NIM, default rate, capital adequacy\n"
                    "- **Retail:** Sales/m², inventory turnover, customer retention\n"
                    "- **Manufacturing:** OEE, defect rate, on-time delivery\n\n"
                    "What industry are you in? I'll suggest the right KPIs."
                )
            return (
                "I'm your Dashboard Designer! I can:\n\n"
                "- Auto-create dashboards from your data\n"
                "- Recommend KPIs for your industry\n"
                "- Choose the best chart types\n"
                "- Design layouts for any audience\n"
                "- Suggest color schemes and styles\n\n"
                "What kind of dashboard do you need?"
            )

        return "How can I help you with your data today?"
