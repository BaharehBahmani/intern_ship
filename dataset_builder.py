import sys
import csv
import typer
import pretty_errors  # keep the import to have better error messages

from os import listdir
from os.path import isfile
from os.path import join
from loguru import logger
from typer import Option
from datetime import datetime
from pathlib import Path
from typing import List
from typing import Set
from typing import Optional
from typing import Tuple
from tqdm import tqdm


class DatasetManager:
    subreddit_header_name = "subreddit"

    def __init__(self, output_path: str, subreddit_dir: str, run_id: str,  caching_size: int):
        self.comments_rows = []
        self.submissions_rows = []
        self.total_comments = 0
        self.total_submissions = 0
        self.comments_census_ids = set()
        self.submissions_census_ids = set()
        self.subreddit_name = "undefined"
        self.output_path = output_path
        self.subreddit_dir = subreddit_dir
        self.caching_size = caching_size
        self.comments_csv_header: Optional[List[str]] = None
        self.submissions_csv_header: Optional[List[str]] = None

        self.run_id = run_id #datetime.today().strftime('%Y%m%d%H%M%S')
        self.runtime_dir = join(self.output_path, self.subreddit_dir, self.run_id)
        self.comments_output_path = join(self.runtime_dir, "comments.csv")
        self.submissions_output_path = join(self.runtime_dir, "submissions.csv")
        Path(self.runtime_dir).mkdir(parents=True, exist_ok=True)

    def set_subreddit(self, subreddit_name: str):
        self.subreddit_name = subreddit_name

    def set_comments_csv_header(self, comments_header: List[str]):
        if not self.comments_csv_header:
            self.comments_csv_header = [DatasetManager.subreddit_header_name] + comments_header

    def set_submissions_csv_header(self, comments_header: List[str]):
        if not self.submissions_csv_header:
            self.submissions_csv_header = [DatasetManager.subreddit_header_name] + comments_header

    def _flush_comments(self):
        self.store_comments()
        self.comments_rows = []

    def _flush_submissions(self):
        self.store_submissions()
        self.submissions_rows = []

    def _rows_parser(self,
                     rows: List[List[str]],
                     census_ids: Set[str],
                     header: List[str]):
        # TODO find a more efficient way to store only unique `id`,
        #  maybe leveraging the Python set structure
        rows_to_remove = []
        for idx, row in enumerate(rows):
            if not row:  # see README.md:notes:
                continue
            row.insert(0, self.subreddit_name)
            row_values = dict(zip(header, row))
            row_id = row_values["id"]
            if row_id in census_ids:
                logger.debug(f"Find duplicate id '{row_id}'")
                rows_to_remove.append(idx)
            census_ids.add(row_id)

        for idx in sorted(rows_to_remove, reverse=True):  # https://stackoverflow.com/a/11303234
            del rows[idx]

    def populate_comments(self, rows: List[List[str]]):
        self._rows_parser(rows, self.comments_census_ids, self.comments_csv_header)
        self.total_comments += len(rows)
        self.comments_rows.extend(rows)
        if len(self.comments_rows) > self.caching_size:
            self._flush_comments()

    def populate_submissions(self, rows: List[List[str]]):
        self._rows_parser(rows, self.submissions_census_ids, self.submissions_csv_header)
        self.total_submissions += len(rows)
        self.submissions_rows.extend(rows)
        if len(self.submissions_rows) > self.caching_size:
            self._flush_submissions()

    def store_comments(self):
        csv_writer(self.comments_output_path, self.comments_csv_header, self.comments_rows)

    def store_submissions(self):
        csv_writer(self.submissions_output_path, self.submissions_csv_header, self.submissions_rows)


def init(debug: bool):
    logger.add(lambda msg: tqdm.write(msg, end=""))
    if not debug:
        logger.remove()
        logger.add(sys.stderr, level="INFO")


def csv_writer(csv_path: str, header: List[str], rows: List[List[str]]):
    skip_header = isfile(csv_path)  # If file already exist, don't write the header

    with open(csv_path, "a+", newline='', encoding="utf-8") as f:
        logger.debug(f"Storing data on '{csv_path}' - header:'{header}'")
        file_writer = csv.writer(f, dialect="excel")
        if not skip_header:
            file_writer.writerow(header)
        file_writer.writerows(rows)


def csv_reader(csv_path: str) -> Tuple[List[str], List[List[str]]]:
    header = None
    rows = []
    with open(csv_path, newline='', encoding="utf-8") as csv_file:
        file_reader = csv.reader(csv_file, dialect="excel")
        for row_id, row in enumerate(file_reader):
            if row_id == 0:
                header = row
                logger.debug(f"File '{csv_path}' header: '{header}'")
                continue
            rows.append(row)
    return header, rows


class HelpMessages:
    """
    Utility class to try maintain clean the `main` function signature
    """
    input_dir = "Main directory with scraped data and this structure: " \
                "`/<subreddit>/<timestamp>/[comments | submission]`"
    run_id = "sub directory with scraped data and this structure: " \
             "`/<subreddit>/<run_id>/[comments | submission]`"   
    output_dir = "Optional output directory"
    subreddit_dir = "Optional output directory"
    config_size = "Store data on the output each `caching_size` number of comments"
    debug = "Enable debug logging"


def main(input_dir: str = Option("./data/", help=HelpMessages.input_dir),
         output_path: str = Option("./dataset/", help=HelpMessages.output_dir),
         subreddit_dir: str = Option("./dataset/", help=HelpMessages.subreddit_dir),
         run_id: str = Option("./dataset/", help=HelpMessages.run_id), # used for both /data/subreddit/run_id and /dataset/subreddit/run_id
         caching_size: int = Option(1000, help=HelpMessages.config_size),
         debug: bool = Option(False, help=HelpMessages.debug),
         ):
    init(debug)
    dataset_mng = DatasetManager(output_path, subreddit_dir, run_id, caching_size)

    #for subreddit_name in tqdm(listdir(input_dir)):  # <input_dir>/<sub>
    subreddit_name = subreddit_dir
    subreddit_path = join(input_dir, subreddit_name, run_id)
    if isfile(subreddit_path):
        return
    logger.debug(f"Start parsing subreddit `{subreddit_name}` data")
    dataset_mng.set_subreddit(subreddit_name)

    #for job_id in tqdm(listdir(subreddit_path)):  # <input_dir>/<subreddit>/<run_id>
    #    job_folder_path = join(subreddit_path, job_id)
    comments_folder_path = join(subreddit_path, "comments")
    submissions_folder_path = join(subreddit_path, "submissions")

    for csv_filename in listdir(comments_folder_path):  # <input_dir>/<subreddit>/<run_id>/comments/<file>.csv
        csv_path = join(comments_folder_path, csv_filename)
        if not isfile(csv_path):
            continue
        header, rows = csv_reader(csv_path)
        dataset_mng.set_comments_csv_header(header)
        dataset_mng.populate_comments(rows)
    logger.debug(f"Comments for job `{run_id}` loaded")

    for csv_filename in listdir(submissions_folder_path):  # <input_dir>/<subreddit>/<run_id>/submissions/<file>.csv
        csv_path = join(submissions_folder_path, csv_filename)
        if not isfile(csv_path):
            continue  # skip `raw` folder
        header, rows = csv_reader(csv_path)
        dataset_mng.set_submissions_csv_header(header)
        dataset_mng.populate_submissions(rows)
    logger.debug(f"Submissions for job `{run_id}` loaded")

    logger.debug(f"Storing data for `{subreddit_name}`")
    dataset_mng.store_comments()
    dataset_mng.store_submissions()


if __name__ == '__main__':
    typer.run(main)
