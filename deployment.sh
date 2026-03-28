adk deploy cloud_run \
  --project=my-lab-project-491212 \
  --region=us-central1 \
  --service_name=netflix-alloydb-agent \
  --app_name=netflix_titles_agent \
  --temp_folder=./deploy \
  --with_ui \
  ./netflix_titles_agent