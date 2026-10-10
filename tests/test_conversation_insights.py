from personal_document_intelligence_api.insights.service import build_conversation_insights


def test_build_conversation_insights_extracts_takeaways_and_ranked_actions() -> None:
    insights = build_conversation_insights(
        [
            (
                "What should we do next?",
                "- Review the source evidence before publishing.\n"
                "- The retrieval index keeps project documents isolated.",
            ),
            (
                "Is the deadline documented?",
                "The answer cannot be found in the documents.",
            ),
        ]
    )

    assert len(insights.takeaways) == 2
    assert insights.takeaways[0].source_turn_numbers == (1,)
    assert [action.rank for action in insights.actions] == [1, 2]
    assert insights.actions[0].priority == "high"
    assert insights.actions[0].kind == "open_question"
    assert insights.actions[1].kind == "recommendation"


def test_build_conversation_insights_does_not_invent_actions() -> None:
    insights = build_conversation_insights(
        [("What is cash flow?", "Cash flow describes money entering and leaving a business.")]
    )

    assert insights.takeaways
    assert insights.actions == ()
