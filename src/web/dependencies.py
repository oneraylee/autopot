from api.analysis_routes import AnalysisRoutes
from api.dataset_routes import DatasetRoutes
from api.export_routes import ExportRoutes
from api.job_routes import JobRoutes
from api.project_routes import ProjectRoutes
from api.proposal_routes import ProposalRoutes
from repositories.artifact_repository import ArtifactRepository
from repositories.dataset_repository import DatasetRepository
from repositories.job_repository import JobRepository
from repositories.project_repository import ProjectRepository
from repositories.scene_label_repository import SceneLabelRepository
from services.job_service import JobService


class AppContainer:
    def __init__(self) -> None:
        self.project_repository = ProjectRepository()
        self.dataset_repository = DatasetRepository()
        self.scene_label_repository = SceneLabelRepository()
        self.job_repository = JobRepository()
        self.artifact_repository = ArtifactRepository()

        self.job_service = JobService(
            job_repository=self.job_repository,
            dataset_repository=self.dataset_repository,
        )

        self.project_routes = ProjectRoutes(project_repository=self.project_repository)
        self.dataset_routes = DatasetRoutes(
            dataset_repository=self.dataset_repository,
            scene_label_repository=self.scene_label_repository,
        )
        self.job_routes = JobRoutes(job_service=self.job_service, job_repository=self.job_repository)
        self.analysis_routes = AnalysisRoutes(
            job_repository=self.job_repository,
            artifact_repository=self.artifact_repository,
        )

        created_jobs: list[dict] = []

        def _create_training_job(candidate: dict) -> dict:
            created_jobs.append(candidate)
            return {"job_id": f"job-{len(created_jobs)}"}

        self.proposal_routes = ProposalRoutes(create_training_job=_create_training_job)
        self.export_routes = ExportRoutes(
            job_repository=self.job_repository,
            artifact_repository=self.artifact_repository,
        )
