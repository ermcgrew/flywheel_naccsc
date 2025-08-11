# flywheel_naccsc

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
  - add_session_tag(session, study)
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
