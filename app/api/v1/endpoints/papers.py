from typing import Optional
from app.schemas.papers import DOIPaperCreate
from fastapi import APIRouter, Depends, Form, HTTPException, status, BackgroundTasks, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.db.database import get_db
from app.core.config import settings
from app.services.auth import get_current_active_user
from app.models.user import User
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

from app.services.papers import doi_fetch

router = APIRouter()

@router.post("/add/doi/{project_id}")
async def add_paper_by_doi(
    project_id: int,
    paper: DOIPaperCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    
    try:
        res = doi_fetch(paper.doi)
        if res[2]=="None Information":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No information found for given DOI."
            )
        if res[2] == 'DOI Service Error 404':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid DOI. Please try again with a valid DOI."
            )
        if res[2]!="OK":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res[2]
            )
        comma_separated_authors = res[0]['authors'].replace(';', ',')
        publish_date2 = res[0]['pub_date']
        # Create new paper entry
        db_paper = Paper(
            paper_id=paper.doi,
            paper_id_type=PaperIdTypeEnum.DOI,
            upload_type=UploadTypeEnum.DOI,
            nct_number = paper.nct_number,
            upload_decision=paper.decision,
            upload_source=UploadSourceEnum.MANUAL,
            title = res[0]['title'],
            abstract = res[0]['abstract'],
            publish_date = publish_date2,
            authers = comma_separated_authors,
            journal = res[0]['journal'],
            project_id = project_id
        )

        db.add(db_paper)
        db.commit()

        is_duplicate = check_duplicate_for_new_paper(db_paper, db)

        if not is_duplicate:
            if paper.decision == DecisionEnum.IncludeInSR or paper.decision == DecisionEnum.IncludeInSRAndMA:
                db_paper.decision = ScreeningDecision.IncludeByFullText
                default_clinical_question = db.query(ClinicalQuestion).filter(
                    ClinicalQuestion.project_id == project_id,
                    ClinicalQuestion.is_default == True,
                    ClinicalQuestion.is_deleted == False
                ).first()
                if default_clinical_question:
                    db_paper_cq = PaperCQ(
                        paper_id = db_paper.id,
                        cq_id = default_clinical_question.id,
                        decision = CQDecision.Include
                    )
                    db.add(db_paper_cq)
                    db.commit()
                    db.refresh(db_paper_cq)
            elif paper.decision == DecisionEnum.ExcludedByFullText:
                db_paper.decision = ScreeningDecision.ExcludedByFullText
            else:
                db_paper.decision = paper.decision

            db.commit()
            db.refresh(db_paper)

        return {"message": "The paper has been successfully added to the system."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )