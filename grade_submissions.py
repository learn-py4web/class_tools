import argparse
import csv
import os
import sys
import signal
import time
import multiprocessing

def worker(test, queue):
    grade = test.grade()
    queue.get()
    queue.put(grade)

def main(args):
    # Load the grade.py file
    grade_path, grade_file = os.path.split(args.grade_file)
    sys.path.append(grade_path)
    grader = __import__(grade_file)
    csv_fn = os.path.join(args.assignment_dir, 'grades.csv')
    timeout_sec = float(args.timeout)
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
                    if timeout_sec == 0:
                        grade = test.grade()
                    else:
                        queue = multiprocessing.Queue()
                        queue.put(-1.0)
                        p = multiprocessing.Process(target=worker, args=(test, queue))
                        p.start()
                        p.join(timeout_sec)
                        if p.is_alive():
                            print('Timeout, trying to terminate...')
                            p.terminate() # p.kill() if does not terminate
                            p.join()
                        grade = queue.get()
                        if(grade == -1.0):
                            print("==========Test Timeout==========")
                    print(f"Graded: {student_dir} got {grade}")
                    writer.writerow({'student': student_dir, 'grade': grade})
        print(f"Grades written to {csv_fn}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--grade_file', default=None,
                        help="grade.py file to use for grading.")
    parser.add_argument('-d', '--assignment_dir', default=None,
                        help="Directory containing the student submissions.")
    parser.add_argument('-t', '--timeout', default=0,
                        help='Timeout(s) for a single submission. Grade is -1.0 if timeout.')

    args = parser.parse_args()
    main(args)
    
