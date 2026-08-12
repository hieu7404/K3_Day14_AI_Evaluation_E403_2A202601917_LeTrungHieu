import json
from pathlib import Path

from template import RAGASEvaluator, rerank_by_overlap


TARGET_IDS = ("E04", "E05", "M01", "H05", "A01")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    goldens = _load_json(Path("golden_dataset.json"))
    actuals = _load_json(Path("artifacts/actual_answers.json"))
    golden_by_id = {item["id"]: item for item in goldens["qa_pairs"]}
    actual_by_id = {item["id"]: item for item in actuals["answers"]}
    evaluator = RAGASEvaluator()

    print(
        f"{'ID':<5} | {'Recall B':<8} | {'Recall A':<8} | "
        f"{'Prec B':<8} | {'Prec A':<8} | Delta P"
    )
    print("-" * 65)

    rows: list[tuple[float, float, float, float]] = []
    for qid in TARGET_IDS:
        golden = golden_by_id[qid]
        actual = actual_by_id[qid]
        expected_answer = golden["expected_answer"]
        retrieved_texts = [ctx["text"] for ctx in actual["retrieved_contexts"]]

        recall_before = evaluator.evaluate_context_recall(
            retrieved_texts, expected_answer
        )
        precision_before = evaluator.evaluate_context_precision(
            retrieved_texts, expected_answer
        )
        reranked_texts = rerank_by_overlap(retrieved_texts, actual["question"])
        recall_after = evaluator.evaluate_context_recall(
            reranked_texts, expected_answer
        )
        precision_after = evaluator.evaluate_context_precision(
            reranked_texts, expected_answer
        )
        rows.append(
            (recall_before, recall_after, precision_before, precision_after)
        )
        print(
            f"{qid:<5} | {recall_before:<8.3f} | {recall_after:<8.3f} | "
            f"{precision_before:<8.3f} | {precision_after:<8.3f} | "
            f"{precision_after - precision_before:+.3f}"
        )

    averages = [sum(column) / len(rows) for column in zip(*rows)]
    recall_before, recall_after, precision_before, precision_after = averages
    print("-" * 65)
    print(
        f"Avg   | {recall_before:<8.3f} | {recall_after:<8.3f} | "
        f"{precision_before:<8.3f} | {precision_after:<8.3f} | "
        f"{precision_after - precision_before:+.3f}"
    )


if __name__ == "__main__":
    main()
