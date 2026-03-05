from copy import deepcopy


class EvidencePackBuilderService:
    def __init__(self, *, max_curve_points: int = 20) -> None:
        self._max_curve_points = max_curve_points

    def build(
        self,
        *,
        dataset_report: dict,
        job_summary: dict,
        eval_report: dict,
        kpi_config: dict,
        artifacts: dict,
    ) -> dict:
        eval_copy = deepcopy(eval_report)
        curves = eval_copy.get("curves")
        if isinstance(curves, dict):
            for curve_name, values in list(curves.items()):
                if isinstance(values, list) and len(values) > self._max_curve_points:
                    curves[curve_name] = self._downsample(values)

        return {
            "dataset_report": deepcopy(dataset_report),
            "job_summary": deepcopy(job_summary),
            "eval_report": eval_copy,
            "kpi_config": deepcopy(kpi_config),
            "index_paths": deepcopy(artifacts),
        }

    def _downsample(self, values: list) -> list:
        if len(values) <= self._max_curve_points:
            return list(values)
        if self._max_curve_points <= 1:
            return [values[0]]

        step = (len(values) - 1) / (self._max_curve_points - 1)
        picked = []
        for i in range(self._max_curve_points):
            picked.append(values[round(i * step)])
        return picked
