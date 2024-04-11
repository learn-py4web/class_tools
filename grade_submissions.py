import argparse
import csv
import os
import sys


def main(args):
    # Load the grade.py file
    grade_path, grade_file = os.path.split(args.grade_file)
    sys.path.append(grade_path)
    grader = __import__(grade_file)
    csv_fn = os.path.join(args.assignment_dir, 'grades.csv')
    with open(csv_fn, 'w', newline='') as csvfile:
        fieldnames=['student', 'grade']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        with os.scandir(args.assignment_dir) as it:
            for entry in it:
                if entry.is_dir() and "@" in entry.name:
                    student_dir = entry.name
                    print("Grading", student_dir)
                    student_path = os.path.join(args.assignment_dir, student_dir)
                    test = grader.Assignment(student_path)
                    grade = test.grade()
                    print(f"Graded: {student_dir} got {grade}")
                    writer.writerow({'student': student_dir, 'grade': grade})
        print(f"Grades written to {csv_fn}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--grade_file', default=None,
                        help="grade.py file to use for grading.")
    parser.add_argument('-d', '--assignment_dir', default=None,
                        help="Directory containing the student submissions.")

    args = parser.parse_args()
    main(args)
    