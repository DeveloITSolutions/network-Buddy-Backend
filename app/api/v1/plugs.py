"""
API endpoints for plug (target/contact) management.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile

from app.core.dependencies import DatabaseSession, CurrentActiveUser
from app.core.exceptions import ValidationError, BusinessLogicError, NotFoundError
from app.schemas.plug import PlugResponse, PlugListResponse
from app.services.plug_service import PlugService
from app.services.plug_profile_service import PlugProfileService

router = APIRouter(tags=["Plugs"])


def get_plug_service(db: DatabaseSession) -> PlugService:
    """Dependency to get plug service instance."""
    return PlugService(db)


def get_plug_profile_service(db: DatabaseSession) -> PlugProfileService:
    """Dependency to get plug profile service instance."""
    return PlugProfileService(db)


# Plug Management Endpoints
@router.post("/", response_model=PlugResponse, status_code=status.HTTP_201_CREATED)
async def create_plug(
    plug_data: dict,  # Accept raw JSON to handle all fields
    current_user: CurrentActiveUser,
    service: PlugService = Depends(get_plug_service)
):
    """
    Create a new plug (target or contact).
    
    - Requires JWT authentication
    - Business logic automatically determines the type based on data completeness
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Create plug through service
        plug = await service.create_plug(user_id, plug_data)
        
        return PlugResponse.model_validate(plug)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.put("/{plug_id}", response_model=PlugResponse)
async def update_plug(
    plug_id: UUID,
    plug_data: dict,  # Accept raw JSON for flexible updates
    current_user: CurrentActiveUser,
    service: PlugService = Depends(get_plug_service)
):
    """
    Update an existing plug (target or contact).
    
    - Requires JWT authentication
    - User can only update their own plugs
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Update plug through service
        plug = await service.update_plug(user_id, plug_id, plug_data)
        
        if not plug:
            raise NotFoundError("Plug not found")
        
        return PlugResponse.model_validate(plug)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{plug_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plug(
    plug_id: UUID,
    current_user: CurrentActiveUser,
    service: PlugService = Depends(get_plug_service)
):
    """
    Delete a plug (soft delete).
    
    - Requires JWT authentication
    - User can only delete their own plugs
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        deleted = await service.delete_plug(user_id, plug_id)
        if not deleted:
            raise NotFoundError("Plug not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=PlugListResponse)
async def list_plugs(
    current_user: CurrentActiveUser,
    # Search and filter parameters
    q: Optional[str] = Query(None, min_length=1, description="Search query (name, company, email, network_type)"),
    plug_type: Optional[str] = Query(None, description="Filter by plug type (target/contact)"),
    network_type: Optional[str] = Query(None, description="Filter by network type (new_client, existing_client, new_partnership, etc.)"),
    status: Optional[str] = Query(None, description="Filter by status (new_client, existing_client, new_partnership)"),
    # Pagination parameters
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    # Service dependency
    service: PlugService = Depends(get_plug_service)
):
    """
    Get paginated list of plugs with search and filtering capabilities.
    
    This unified endpoint handles all plug listing needs:
    - Text search across name, company, email, network_type (when q parameter is provided)
    - Filter by plug type (target/contact)
    - Filter by network type (new_client, existing_client, new_partnership, etc.)
    - Filter by status (new_client, existing_client, new_partnership)
    - Pagination support
    
    Examples:
    - All plugs: GET /
    - Search contacts: ?q=john&plug_type=contact
    - Filter new clients: ?network_type=new_client&plug_type=contact
    - Search by network type: ?q=new_client
    - Filter existing clients: ?network_type=existing_client
    - Search targets: ?q=company&plug_type=target
    - All contacts: ?plug_type=contact
    - All targets: ?plug_type=target
    
    - Requires JWT authentication
    - Returns only the user's own plugs
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Get plugs with optional search and filtering
        plugs, total = await service.get_user_plugs(user_id, plug_type, skip, limit, q, network_type)
        
        # Apply status filter if provided
        if status:
            plugs = [plug for plug in plugs if getattr(plug, 'status', None) == status]
            total = len(plugs)  # Update total after filtering
        
        # Calculate counts for targets and contacts
        target_count = sum(1 for plug in plugs if plug.plug_type.value == 'target')
        contact_count = sum(1 for plug in plugs if plug.plug_type.value == 'contact')
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        current_page = skip // limit + 1
        
        return PlugListResponse(
            items=[PlugResponse.model_validate(plug) for plug in plugs],
            total=total,
            page=current_page,
            per_page=limit,
            pages=pages,
            has_next=current_page < pages,
            has_prev=current_page > 1,
            counts={
                "targets": target_count,
                "contacts": contact_count
            }
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))




@router.get("/{plug_id}", response_model=PlugResponse)
async def get_plug(
    plug_id: UUID,
    current_user: CurrentActiveUser,
    service: PlugService = Depends(get_plug_service)
):
    """
    Get a specific plug (target or contact) by ID.
    
    - Requires JWT authentication
    - User can only access their own plugs
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        plug = await service.get_user_plug(user_id, plug_id)
        
        if not plug:
            raise NotFoundError("Plug not found")
        
        return PlugResponse.model_validate(plug)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Target to Contact Conversion
@router.post("/{target_id}/convert", response_model=PlugResponse)
async def convert_target_to_contact(
    target_id: UUID,
    conversion_data: dict,  # Accept raw JSON for flexible conversion data
    current_user: CurrentActiveUser,
    service: PlugService = Depends(get_plug_service)
):
    """
    Convert a target to a contact with additional information.
    
    - Requires JWT authentication
    - User can only convert their own targets
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        plug = await service.convert_target_to_contact(user_id, target_id, conversion_data)
        
        if not plug:
            raise NotFoundError("Target not found")
        
        return PlugResponse.model_validate(plug)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# Profile Picture Management
@router.post("/{plug_id}/profile-picture", response_model=PlugResponse, tags=["Plugs - Profile"])
async def upload_profile_picture(
    plug_id: UUID,
    current_user: CurrentActiveUser,
    file: UploadFile = File(..., description="Profile picture image file"),
    profile_service: PlugProfileService = Depends(get_plug_profile_service)
):
    """
    Upload or update profile picture for a plug.
    
    - Requires JWT authentication
    - User can only update profile pictures for their own plugs
    - Uploads image to S3 with organized paths
    - Automatically deletes old profile picture if exists
    - Supported formats: JPEG, PNG, GIF, WebP, SVG
    - Maximum file size: 10MB
    - Returns updated plug with new profile picture URL
    
    **Process:**
    1. Validates file type and size
    2. Deletes old profile picture from S3 (if exists)
    3. Uploads new image to S3
    4. Updates plug record with new profile picture URL
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Validate file is provided
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Upload profile picture through service
        updated_plug = await profile_service.upload_profile_picture(
            user_id=user_id,
            plug_id=plug_id,
            file_content=file_content,
            filename=file.filename or "profile.jpg",
            content_type=file.content_type or "image/jpeg"
        )
        
        return PlugResponse.model_validate(updated_plug)
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{plug_id}/profile-picture", response_model=PlugResponse, tags=["Plugs - Profile"])
async def delete_profile_picture(
    plug_id: UUID,
    current_user: CurrentActiveUser,
    profile_service: PlugProfileService = Depends(get_plug_profile_service)
):
    """
    Delete profile picture for a plug.
    
    - Requires JWT authentication
    - User can only delete profile pictures from their own plugs
    - Removes image from S3 storage
    - Updates plug record to remove profile picture URL
    - Returns updated plug without profile picture
    
    **Process:**
    1. Verifies plug ownership
    2. Deletes profile picture from S3 (if exists)
    3. Updates plug record to set profile_picture to null
    """
    try:
        # Extract user_id from JWT token
        user_id = UUID(current_user["user_id"])
        
        # Delete profile picture through service
        updated_plug = await profile_service.delete_profile_picture(
            user_id=user_id,
            plug_id=plug_id
        )
        
        return PlugResponse.model_validate(updated_plug)
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
