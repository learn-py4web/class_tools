# Grading for py4web de Alfaro Assignments

Every assignment has a source version, which is private to instructors and used to develop the grading, and a student version, which is shared with students. 

## Grading

There are two steps in grading an assignment: downloading it, and grading it. 

The package accesses Google Drive; you need to have this credentials.json file. Please do not share it. If it leaks, it does not grant anyone access to anybody else’s Drive, but it still uses resources from a cloud project that is not for public use. 
Downloading an assignment
 python download_submissions.py -s <sheets_id> -d <submission_folder>

where: 

sheets_id is the ID of the google sheets corresponding to the submissions form.  If the URL of the sheet is: 

`https://docs.google.com/spreadsheets/d/something/edit`

then the ID is the `something` portion. 

submission_folder is the directory where you want the result to be stored.  There will be one folder per student, named student@ucsc.edu (with student replaced by the student actual email id), with in it already unzipped, the student submission. 

The download code has many options; feel free to explore them. 

Grading an assignment
To grade an assignment, do: 

```
python grade_submissions.py -d submission_folder -g ../assignment1-source/grade 
```

In other words, 
* `-d` is the folder where the submissions are, 
* `-g` is the path to the grading file in the source assignment, not in the student assignment (students can tamper with it). 

The result will be a grades.csv file in the submissions folder. 

## Uploading grades

This can be done with the [py-canvas](https://github.com/edulinq/py-canvas) package. 
A sample command line is: 

```
python3 -m canvas.cli.assignment.upload-scores --config <path_to_config.json> --course <course_number> <assignment_number> path/to/grades.csv --skip-rows 1
```

You can get the assignment number by listing the assignments, via: 

```
python3 -m canvas.cli.assignment.list --config <path_to_config.json> --course <course_number>
```



