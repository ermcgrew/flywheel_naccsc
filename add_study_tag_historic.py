#!/usr/bin/env python3

import flywheel
import logging

# Real version:
logging.basicConfig(filename="log_add_study_tag_historic_20231024_9_27am.txt", 
                    filemode='w', format='%(levelname)s:%(message)s', level=logging.DEBUG)
# for testing:
# logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
    
studylist = ["ABC", "ABCD2", "VCID", "LEADS", "YMTL", "MPC"]

fw = flywheel.Client()
if not fw:
    logging.critical("Unable to establish flywheel client")

# NACC-SC flywheel project by ID
try:
    project = fw.get_project("5c508d5fc2a4ad002d7628d8")
except flywheel.ApiException:
    logging.critical("Unable to access NACC-SC project")    

# get list of sessions
try:
    # Real version:
    sessions = project.sessions.iter_find()
    # for testing:
    # sessions = project.sessions.iter_find("label=CAMRIS^Wolk")
except flywheel.ApiException:
    logging.exception("Exception occurred when finding sessions")

for session in sessions:
    sessionlabellist = session.label.rsplit("x", 3)
    if len(sessionlabellist) == 4:
        study = sessionlabellist[-1]
        if study in studylist:
            try:
                session.add_tag(study)
                #will always add to session, since I have admin permission? but doesn't add it to group tag list?
                logging.info(f"{study}:{session.label}:Added study as tag to session") 
            except flywheel.ApiException:
                logging.debug(f"{study}:{session.label}:Session already tagged with study")

        else:
            logging.debug(f"{study}:{session.label}:Not a study")
    else:
        logging.debug(f"{session.label}:Not long enough for study tag")
