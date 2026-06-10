import json
import re
from datetime import date, datetime, timedelta


DATA_FILE = "habits.json"
LOG_FILE = "log.txt"
IMPORT_FILE = "HabitData.txt"

class HabitTrackerError(Exception):
    """Custom exception for habit handling errors."""


def log_action(function):
    """A custom decorator that writes actions to a file defined by the LOG_FILE constant."""
    def wrapper(*args, **kwargs):
        try:
            result = function(*args, **kwargs)
            status = "OK"
            return result
        except Exception as error:
            status = "ERROR: " + str(error)
            raise
        finally:
            with open(LOG_FILE, "a", encoding="utf-8") as file:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                file.write(now + " | " + function.__name__ + " | " + status + "\n")
    return wrapper


def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"habits": {}}
    except json.JSONDecodeError:
        raise HabitTrackerError(f"File {DATA_FILE} is damaged.")


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def clean_name(name):
    return re.sub(r"\s+", " ", name.strip().lower())


def validate_name(name):
    name = clean_name(name)
    pattern = r"^[a-ząćęłńóśźż0-9][a-ząćęłńóśźż0-9 \-]{2,39}$"

    if not re.match(pattern, name):
        raise HabitTrackerError("The name must be 3-40 characters long: letters, numbers, spaces or a dash.")

    return name


def validate_date(text):
    if text == "":
        return date.today().isoformat()

    try:
        chosen_date = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise HabitTrackerError("The date must have a format YYYY-MM-DD.")

    if chosen_date > date.today():
        raise HabitTrackerError("Cannot add execution in the future.")

    return chosen_date.isoformat()


def days_generator(how_many):
    """Latest days generator."""
    today = date.today()

    for number in range(how_many - 1, -1, -1):
        yield today - timedelta(days=number)


@log_action
def add_habit(data):
    name = validate_name(input("Habit name: "))

    if name in data["habits"]:
        raise HabitTrackerError("This habit already exists.")

    data["habits"][name] = []
    save_data(data)
      print("Added:", name)


@log_action
def mark_done(data):
    name = validate_name(input("Habit name: "))

    if name not in data["habits"]:
        raise HabitTrackerError("This habit doesn't exists.")

    day = validate_date(input("Data YYYY-MM-DD, Enter = today: "))

    if day in data["habits"][name]:
        raise HabitTrackerError("This habit is already marked on this day.")

    data["habits"][name].append(day)
    data["habits"][name].sort()
    save_data(data)
    print("Execution has been saved:", name, day)


@log_action
def remove_habit(data):
    name = validate_name(input("Name of the habit to be removed: "))

    if name not in data["habits"]:
        raise HabitTrackerError("This habit doesn't exists.")

    del data["habits"][name]
    save_data(data)
    print("Deleted:", name)


def count_streak(records):
    records_set = set(records)
    streak = 0

    while (date.today() - timedelta(days=streak)).isoformat() in records_set:
        streak = streak + 1

    return streak


def show_habits(data):
    if len(data["habits"]) == 0:
        print("Lack of habbits.")
        return

    habits = sorted(data["habits"].items(), key=lambda item: len(item[1]), reverse=True)

    print("\nHABITS:")
    for number, item in enumerate(habits, start=1):
        name = item[0]
        records = item[1]
        print(str(number) + ". " + name + " | execution: " + str(len(records)))


def show_stats(data):
    if len(data["habits"]) == 0:
        print("No data available for statistics.")
        return
      
    totals = {name: len(records) for name, records in data["habits"].items()}

    active_habits = [name for name, total in totals.items() if total > 0]

    active_days = {day for records in data["habits"].values() for day in records}

    all_done = sum(totals.values())
    average = all_done / len(data["habits"]) if len(data["habits"]) > 0 else 0

    print("\nSTATS:")
    print("Number of habits:", len(data["habits"]))
    print("Active habits:", len(active_habits))
    print("All versions:", all_done)
    print("Average performance per habit:", round(average, 2))
    print("Days of activity:", len(active_days))

    print("\nDetails:")
    for name, records in data["habits"].items():
        print("- " + name + ": " + str(len(records)) + " performances, streak: " + str(count_streak(records)))


def show_last_7_days(data):
    print("\nLAST 7 DAYS:")

    for day in days_generator(7):
        day_text = day.isoformat()

        done_today = (
            name for name, records in data["habits"].items()
            if day_text in records
        )

        done_today = list(done_today)

        if len(done_today) > 0:
            print(day_text + ": " + ", ".join(done_today))
        else:
            print(day_text + ": None")


@log_action
def import_from_file(data):
    try:
        with open(IMPORT_FILE, "r", encoding="utf-8") as file:
            text = file.read()
    except FileNotFoundError:
        raise HabitTrackerError(f"File not found {IMPORT_FILE}.")

    found = re.findall(r"drinking water|running|cooking|playing|cleaning", text, re.IGNORECASE)

    if len(found) == 0:
        raise HabitTrackerError("No matching habits found in the file.")

    unique_found = {clean_name(item) for item in found}
    added = 0

    for name in unique_found:
        if name not in data["habits"]:
            data["habits"][name] = []
            added = added + 1

    save_data(data)
    print("Import done. added:", added)

def choose_an_option(choice, data):
    try:
        match choice:
            case "1":
                print("Showing data...")
                show_habits(data)

            case "2":
                print("Adding habbit...")
                add_habit(data)
                data = load_data()

            case "3":
                print("Performance marking...")
                mark_done(data)
                data = load_data()

            case "4":
                print("Removing a habit...")
                remove_habit(data)
                data = load_data()

            case "5":
                print("View statistics...")
                show_stats(data)

            case "6":
                print("Importing data...")
                import_from_file(data)
                data = load_data()

            case "7":
                print("Viewing the last 7 days...")
                show_last_7_days(data)

            case "0":
                print("Exit program.")
                exit(0)

            case _:
                print("There is no such option.")

    except HabitTrackerError as error:
        print("Błąd:", error)
    except OSError as error:
        print("Błąd pliku:", error)

def show_menu():
    print("\n=== HABIT TRACKER ===")
    print("1. Show habits")
    print("2. Add habbit")
    print("3. Performance marking")
    print("4. Delete a habit")
    print("5. Stats")
    print("6. Importing data from HabitData.txt")
    print("7. Last 7 days")
    print()
    print("0. Exit program")


def main():
    try:
        data = load_data()
    except HabitTrackerError as error:
        print("Error:", error)
        data = {"habits": {}}
    except OSError as error:
        print("File error:", error)
        data = {"habits": {}}
    except Exception as error:
        print("Unexpected error:", error)
        data = {"habits": {}}

    while True:
        show_menu()
        choice = input("Select an option: ").strip()

        choose_an_option(choice, data)


if __name__ == "__main__":
    main()
