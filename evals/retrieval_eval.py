from collections import Counter

from evals.dataset import EVAL_CASES
from rag.retriever import CodeRetriever


def evaluate_case(case: dict, k: int = 3) -> dict:
    retriever = CodeRetriever(
        repository=case["repository"],
        k=k,
    )

    documents = retriever.invoke(case["question"])

    retrieved_files = []

    for document in documents:
        file_path = document.metadata["file_path"]

        if file_path not in retrieved_files:
            retrieved_files.append(file_path)

        expected_files = set(case["expected_files"])

        # Rank of the first relevant file
        first_relevant_rank = None

        for rank, file_path in enumerate(retrieved_files, start=1):
            if file_path in expected_files:
                first_relevant_rank = rank
                break

    return {
        "question": case["question"],
        "expected_files": list(expected_files),
        "retrieved_files": retrieved_files,
        "hit_at_1": (
            bool(retrieved_files)
            and retrieved_files[0] in expected_files
        ),
        "hit_at_3": first_relevant_rank is not None,
        "reciprocal_rank": (
            1 / first_relevant_rank
            if first_relevant_rank is not None
            else 0
        ),
    }


def run_evaluation(k: int = 3):
    results = [
        evaluate_case(case, k=k)
        for case in EVAL_CASES
    ]

    total = len(results)

    hit_at_1 = sum(
        result["hit_at_1"]
        for result in results
    ) / total

    hit_at_3 = sum(
        result["hit_at_3"]
        for result in results
    ) / total

    mrr = sum(
        result["reciprocal_rank"]
        for result in results
    ) / total

    print("\nRepoPilot Retrieval Evaluation")
    print("=" * 35)

    print(f"Cases:  {total}")
    print(f"Hit@1:  {hit_at_1:.2%}")
    print(f"Hit@3:  {hit_at_3:.2%}")
    print(f"MRR:    {mrr:.3f}")

    print("\nIndividual Results")
    print("-" * 35)

    for result in results:
        status = "PASS" if result["hit_at_3"] else "FAIL"

        print(f"\n[{status}] {result['question']}")
        print(f"Expected:  {result['expected_files']}")
        print(f"Retrieved: {result['retrieved_files']}")

    return results


if __name__ == "__main__":
    run_evaluation()