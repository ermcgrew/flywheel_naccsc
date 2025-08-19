#!/usr/bin/env python3

"""
This script runs weekly via cron job set up by Emily on bscsub cluster. 
It checks that new flywheel session names have the correct format and fixes them, if enough information is present. 
Study name tag applied to session.
If session is 3T, IF_todo tag applied.
When all sessions reviewed, run create_reader_task gear to make Incidental Finding tasks for all new 3T sessions. 
Log is emailed to Emily, who manually fixes any sessions with unknown information.

Fuctions:
- main()
  - check_correct(sessionlabellist, subject, date)
  - rename_session(session, subject, date)
  - IF_todo_tag(session)
  - create_IF_todo_tasks(fw,project)
- email_log(logfilepath)
- parse_log(logfilepath,logdir)

Log levels
- Debug: correct session label or tag on session
- Info: renamed session label
- Warning: incorrectly formatted subject label OR insufficient information for full renaming
- Error: tag not added or gear not run because of some exception
- Critical: unable to establish connection to flywheel client

detailed logs of each weekly run are saved at 
/project/wolk/Prisma3T/relong/naccsc_fw_session_rename_logs/log_check_new_session_names_{datetime}.txt
- get list of renamed sessions with: `cat log_check_new_session_names_{datetime}.txt | grep INFO | cut -d ":" -f 3,4`  
- get list of items needing attention with: `cat log_check_new_session_names_{datetime}.txt | grep WARNING`

log of all session names changed by this script, in the format old name:new name:date changed, are saved at 
/project/wolk/Prisma3T/relong/naccsc_fw_session_rename_logs/all_fw_session_renames.txt
"""

import flywheel
import logging
from datetime import datetime, timedelta
import os
from config import log_email,IF_email


def check_correct(sessionlabellist, subject, date):
    if (
        len(sessionlabellist) == 4
        and sessionlabellist[0] == subject
        and sessionlabellist[1] == date
        and sessionlabellist[2] in scantypelist
        and sessionlabellist[3] in studylist
    ):
        return True
    else:
        return False


def rename_session(session, subject, date):
    scantype = ""
    study = ""
    datadict = {
        "MagneticFieldStrength": "",
        "InstitutionName": "",
        "InstitutionAddress": "",
        "PerformedProcedureStepDescription": "",
        "ProtocolName": "",
    }

    for acquisition in session.acquisitions():
        modality = acquisition.files[0].modality
        if modality == "CT" or modality == "SR":
            # those acquisitions don't have detailed metadata
            continue
        else:
            acquisition = acquisition.reload()

            # all acq.labels into 1 string to be partial-matched to
            labels = " ".join(
                [acquisition.label for acquisition in session.acquisitions()]
            )

            # only need the dicom file's metadata
            dicom_file_index = [
                x
                for x in range(0, len(acquisition.files))
                if acquisition.files[x].type == "dicom"
            ][0]
            file_info = acquisition.files[dicom_file_index].info
            # populate datadict with info, error if key not found
            for key in datadict:
                try:
                    datadict[key] = file_info[key]
                except KeyError:
                    pass

            if modality == "PT":
                if "Amyloid" in labels or "AV45" in labels:
                    if "lorbetapir" in session.label:
                        scantype = "FlorbetapirPET"
                        logging.warning(
                            f"{session.label}: Florbetapir scan, double check"
                            )
                    else:
                        scantype = "FBBPET"
                    if (
                        "844047" in datadict["PerformedProcedureStepDescription"]
                        or "844047" in datadict["ProtocolName"]
                    ):
                        study = "ABCD2"
                        break
                    elif (
                        "825943" in datadict["PerformedProcedureStepDescription"]
                        or "825943" in datadict["ProtocolName"]
                    ):
                        study = "ABC"
                        break
                    elif (
                        "829602" in datadict["PerformedProcedureStepDescription"]
                        or "829602" in datadict["ProtocolName"]
                    ):
                        study = "LEADS"
                        break
                    elif (
                        "850160" in datadict["PerformedProcedureStepDescription"]
                        or "850160" in datadict["ProtocolName"]
                        or "850679" in datadict["PerformedProcedureStepDescription"]
                        or "850679" in datadict["ProtocolName"]
                    ):
                        study = "MPC"    
                    else:
                        continue
                elif "2620" in labels:
                    # PI2620 sometimes listed with space--PI 2620
                    scantype = "PI2620PET"
                    study = "ABC"
                    break
                elif "AV1451" in labels:
                    scantype = "AV1451PET"
                    if (
                        "844403" in datadict["PerformedProcedureStepDescription"]
                        or "844403" in datadict["ProtocolName"]
                    ):
                        study = "ABCD2"
                        break
                    elif (
                        "825944" in datadict["PerformedProcedureStepDescription"]
                        or "833864" in datadict["PerformedProcedureStepDescription"]
                        or "825944" in datadict["ProtocolName"]
                        or "833864" in datadict["ProtocolName"]
                    ):
                        study = "ABC"
                        break
                    elif (
                        "829602" in datadict["PerformedProcedureStepDescription"]
                        or "829602" in datadict["ProtocolName"]
                    ):
                        study = "LEADS"
                        break
                    elif (
                        "850160" in datadict["PerformedProcedureStepDescription"]
                        or "850160" in datadict["ProtocolName"]
                        or "850679" in datadict["PerformedProcedureStepDescription"]
                        or "850679" in datadict["ProtocolName"]
                    ):
                        study = "MPC"
                        break 
                    else:
                        continue
                elif "FDG" in labels:
                    scantype = "FDGPET"
                    study = "LEADS"
                    break
                else:
                    break

            elif modality == "MR":
                if round(datadict["MagneticFieldStrength"]) == 7:
                    scantype = "7T"
                    if session.label[-4:] == "YMTL":
                        study = "YMTL"
                        break
                    else:
                        study = "ABC"
                        break
                elif datadict["MagneticFieldStrength"] == 3:
                    scantype = "3T"
                    if (
                        datadict["InstitutionName"] == "HUP"
                        or "Spruce" in datadict["InstitutionAddress"]
                    ):
                        if "Axial" in labels:
                            study = "LEADS"
                            break
                        elif "LLASL" in labels:
                            study = "VCID"
                            break
                        else:
                            continue
                    elif (
                        datadict["InstitutionName"] == "SC3T"
                        or "Curie" in datadict["InstitutionAddress"]
                    ):
                        if session.label[-4:] == "YMTL":
                            study = "YMTL"
                            break
                        elif session.label[-5:] == "ABCD2":
                            study = "ABCD2"
                            break
                        elif session.label[-3:] == "ABC":
                            study = "ABC"
                            break
                        elif session.label[-3:] == "MPC":
                            study = "MPC"
                        else:
                            break
                    else:
                        continue
                else:
                    continue

    tag_with_study(session, study)
    return subject + "x" + date + "x" + scantype + "x" + study


def tag_with_study(session,study):
    if study in session.tags:
        logging.debug(f"{session.label}:session already tagged with study {study}.")
    else:
        try:
            session.add_tag(study)
            logging.debug(f"{session.label}:{study}:Study added as tag to session") 
        except:
            logging.error(f"{session.label}:An error occurred when tagging with study {study}")


def IF_todo_tag(session):
    if "IF_todo" in session.tags:
        logging.debug(f"{session.label}:session already tagged with IF_todo")
    else:
        try:
            session.add_tag("IF_todo")
            logging.debug(f"{session.label}:IF_todo: IF_todo added as tag to session")
        except:
            logging.error(f"{session.label}:An error occurred when tagging with 'IF_todo'")


def create_IF_todo_tasks(fw,project):
    config = {
        "task_type": "Incidential_findings",
        "assignee": f"{IF_email}",
        "due_date": "",
        "container_level": "session",
        "include_tags": "IF_todo"
    }
    inputs={}

    gear = fw.lookup(f'gears/create-guided-reader-task')
    try:
        job_id = gear.run(config=config,inputs=inputs,destination=project)
        logging.debug(f"Create_reader_task gear submitted with job id {job_id}. Check flywheel jobs log for status.")
    except:
        logging.error(f"Create_reader_task gear not run.")


def email_log(logfilepath):
    os.system(f'mail -s "Flywheel session name change log" {log_email} < {logfilepath}')


def parse_log(logfilepath,logdir):
    os.system(f'cat {logfilepath} | grep INFO | cut -d ":" -f 3,4,6 >> {logdir}all_fw_session_renames.txt')


def main():
    fw = flywheel.Client(request_timeout=600)
    if not fw:
        logging.critical("Unable to establish flywheel client")

    # NACC-SC flywheel project by ID
    try:
        project = fw.get_project("5c508d5fc2a4ad002d7628d8")
    except flywheel.ApiException:
        logging.exception("Exception occurred")

    weekago_dt = datetime.now() - timedelta(days=7)
    search_string = "created>" + weekago_dt.strftime("%Y-%m-%d")

    # get list of sessions
    try:
        sessions = project.sessions.iter_find(search_string)
    except flywheel.ApiException:
        logging.exception("Exception occurred")

    for session in sessions:
        sessionlabellist = session.label.rsplit("x", 3)
        subject = session.subject.label
        if "." in subject or "_" in subject:
            logging.warning(f"Subejct label {subject} incorrect")

        date = str(session.timestamp)[:10].replace("-", "")

        if check_correct(sessionlabellist, subject, date):
            logging.debug(f"Session label {session.label} is correct")
            ## add IF_todo tag for 3T sessions
            if "3T" in sessionlabellist: 
                IF_todo_tag(session)
            ## add study tag to session
            study = sessionlabellist[-1]
            if study in studylist:
                tag_with_study(session, study)
        else:
            new_session_label = rename_session(session, subject, date)
            logging.info(
                f"Session label renamed from:{session.label}:{new_session_label}: on date:{current_date}"
            )
            if new_session_label[-1:] == "x":
                logging.warning(
                    f"{session.label}:{new_session_label}; insufficient information for scantype and/or study"
                )
            # Uncomment for real version
            session.update({'label': new_session_label})
            ## add IF_todo tag for 3T sessions
            if "3T" in new_session_label: 
                IF_todo_tag(session)

    ## run create_task_gear to make Incidental findings tasks for all new 3T sessions
    create_IF_todo_tasks(fw,project)


scantypelist = ["3T", "7T", "PI2620PET", "FBBPET", "AV1451PET", "FDGPET"]
studylist = ["ABC", "ABCD2", "VCID", "LEADS", "YMTL", "MPC", "ADNI", 'CLARiTI']
current_datetime = datetime.now().strftime("%Y-%m-%dT%H_%M_%S")
current_date = datetime.now().strftime("%Y-%m-%d")
logfilename = f"log_check_new_session_names_{current_datetime}.txt"
logdir = "/project/wolk/Prisma3T/relong/naccsc_fw_session_rename_logs/"
logfilepath = logdir + logfilename

logging.basicConfig(filename=logfilepath, filemode='w', format='%(levelname)s: %(message)s', level=logging.DEBUG)

main()
email_log(logfilepath)
parse_log(logfilepath,logdir)