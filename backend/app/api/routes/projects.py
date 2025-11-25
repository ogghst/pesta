import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import SQLModel, func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    WBE,
    CostElement,
    CostElementCreate,
    Message,
    Project,
    ProjectCreate,
    ProjectPublic,
    ProjectsPublic,
    ProjectUpdate,
    WBECreate,
)
from app.services.branch_filtering import apply_status_filters
from app.services.entity_versioning import (
    create_entity_with_version,
    soft_delete_entity,
    update_entity_with_version,
)

router = APIRouter(prefix="/projects", tags=["projects"])


# Template schemas for bulk import
class WBETemplateItem(SQLModel):
    """WBE with nested cost elements."""

    wbe: dict[str, Any]
    cost_elements: list[dict[str, Any]] = []


class ProjectTemplate(SQLModel):
    """Template for creating a complete project hierarchy."""

    project: dict[str, Any]
    wbes: list[WBETemplateItem] = []


@router.get("/", response_model=ProjectsPublic)
def read_projects(
    session: SessionDep, _current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve projects (active only).
    """
    count_statement = select(func.count()).select_from(Project)
    count_statement = apply_status_filters(count_statement, Project, status="active")
    count = session.exec(count_statement).one()

    statement = select(Project)
    statement = apply_status_filters(statement, Project, status="active")
    statement = statement.offset(skip).limit(limit)
    projects = session.exec(statement).all()

    return ProjectsPublic(data=projects, count=count)


@router.get("/{id}", response_model=ProjectPublic)
def read_project(session: SessionDep, _current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get project by ID (active only).
    """
    statement = select(Project).where(Project.project_id == id)
    statement = apply_status_filters(statement, Project, status="active")
    project = session.exec(statement).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/", response_model=ProjectPublic)
def create_project(
    *, session: SessionDep, _current_user: CurrentUser, project_in: ProjectCreate
) -> Any:
    """
    Create new project.
    """
    project = Project.model_validate(project_in)
    # Set version=1 and status='active'
    project = create_entity_with_version(
        session=session,
        entity=project,
        entity_type="project",
        entity_id=str(project.project_id),
    )
    session.commit()
    session.refresh(project)
    return project


@router.put("/{id}", response_model=ProjectPublic)
def update_project(
    *,
    session: SessionDep,
    _current_user: CurrentUser,
    id: uuid.UUID,
    project_in: ProjectUpdate,
) -> Any:
    """
    Update a project. Creates a new version.
    """
    update_dict = project_in.model_dump(exclude_unset=True)
    try:
        project = update_entity_with_version(
            session=session,
            entity_class=Project,
            entity_id=id,
            update_data=update_dict,
            entity_type="project",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    session.commit()
    session.refresh(project)
    return project


@router.delete("/{id}")
def delete_project(
    session: SessionDep, _current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a project (soft delete: sets status='deleted').
    """
    # Check if project has active WBEs
    wbe_statement = select(func.count()).select_from(WBE).where(WBE.project_id == id)
    from app.services.branch_filtering import apply_branch_filters

    wbe_statement = apply_branch_filters(wbe_statement, WBE, branch="main")
    wbes_count = session.exec(wbe_statement).one()
    if wbes_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete project with {wbes_count} existing WBE(s). Delete WBEs first.",
        )

    # Soft delete: create new version with status='deleted'
    try:
        soft_delete_entity(
            session=session,
            entity_class=Project,
            entity_id=id,
            entity_type="project",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    session.commit()
    return Message(message="Project deleted successfully")


@router.post("/from-template", response_model=ProjectPublic)
def create_project_from_template(
    *, session: SessionDep, _current_user: CurrentUser, template: ProjectTemplate
) -> Any:
    """
    Create a complete project structure from a template.

    This endpoint creates a project with all associated WBEs and cost elements
    in a single transaction. If any part fails, the entire operation is rolled back.
    """
    # Start a transaction explicitly
    try:
        # Create the project from template
        project_data = template.project
        project_create = ProjectCreate(**project_data)
        project = Project.model_validate(project_create)
        session.add(project)
        session.flush()  # Get project_id without committing

        created_wbes = []
        for wbe_item in template.wbes:
            # Create WBE
            wbe_data = wbe_item.wbe.copy()
            wbe_data["project_id"] = project.project_id
            wbe_create = WBECreate(**wbe_data)
            wbe = WBE.model_validate(wbe_create)
            session.add(wbe)
            session.flush()
            created_wbes.append(wbe)

            # Create cost elements for this WBE
            for ce_data in wbe_item.cost_elements:
                ce_data_with_wbe = ce_data.copy()
                ce_data_with_wbe["wbe_id"] = wbe.wbe_id
                ce_create = CostElementCreate(**ce_data_with_wbe)
                ce = CostElement.model_validate(ce_create)
                session.add(ce)

        # Commit all at once
        session.commit()
        session.refresh(project)

        return project
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Failed to create project from template: {str(e)}"
        )
