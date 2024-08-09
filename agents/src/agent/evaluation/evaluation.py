from langchain import hub
from langchain_openai import ChatOpenAI

grade_prompt_answer_accuracy = hub.pull("langchain-ai/rag-answer-vs-reference")

def answer_evaluator(run, example) -> dict:
    """
    A simple evaluator for RAG answer accuracy
    """
    input_question = example.inputs["input"]
    reference = example.outputs["output"]
    prediction = run.outputs["response"]

    llm = ChatOpenAI(model="gpt-4", temperature=0)
    answer_grader = grade_prompt_answer_accuracy | llm

    score = answer_grader.invoke(
        {
            "question": input_question,
            "correct_answer": reference,
            "student_answer": prediction,
        }
    )
    score = score["Score"]
    return {"key": "answer_v_reference_score", "score": score}

def check_trajectory_custom(root_run, example) -> dict:
    """
    Check if all expected tools are called in exact order and without any additional tool calls.
    """
    expected_trajectory_1 = [
        "retrieve_data",
        "grade_data_retrieval",
        "web_search",
        "generate_answer",
    ]
    expected_trajectory_2 = [
        "retrieve_data",
        "grade_data_retrieval",
        "generate_answer",
    ]

    tool_calls = root_run.outputs["steps"]
    print(f"Tool calls custom agent: {tool_calls}")
    if tool_calls == expected_trajectory_1 or tool_calls == expected_trajectory_2:
        score = 1
    else:
        score = 0

    return {"score": int(score), "key": "tool_calls_in_exact_order"}