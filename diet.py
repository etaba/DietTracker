import sqlite3
from functools import reduce
from pprint import pprint
import colorama


DB_FILE = "dietDb.sqlite"
CUT = {"Cal":2000,"Fat":36,"Protein":216,"Carbs":180,"Na":2.3,"K":4.6}
MAINTAIN = {"Cal":2100,"Fat":63,"Protein":180,"Carbs":288,"Na":2.3,"K":4.6}
BULK = {"Cal":2000,"Fat":36,"Protein":216,"Carbs":180,"Na":2.3,"K":4.6}
DIET = MAINTAIN

colorama.init(autoreset=True)



#initialize database and diet tables
def dietInit():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT 1 FROM sqlite_master WHERE type="table" AND name="food"')
    if len(c.fetchall()) == 0:
        c.execute('CREATE TABLE food(name TEXT PRIMARY KEY, calories INTEGER, fat INTEGER, protein INTEGER, carbs INTEGER, sodium INTEGER, potassium INTEGER)')
    c.execute('SELECT 1 FROM sqlite_master WHERE type="table" AND name="meal"')
    if len(c.fetchall()) == 0:
        c.execute('CREATE TABLE meal(mealDate, food, FOREIGN KEY(food) REFERENCES food(name))')
    c.execute('SELECT 1 FROM sqlite_master WHERE type="table" AND name="exercise"')
    if len(c.fetchall()) == 0:
        c.execute('CREATE TABLE exercise(exerciseDate, cal INTEGER)')
    conn.commit()
    conn.close()

def addFood(name, calories, fat, protein, carbs, sodium, potassium):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    qry = 'INSERT INTO food (name, calories, fat, protein, carbs, sodium, potassium) VALUES ("{}",{},{},{},{},{},{})'.format(name, calories, fat, protein, carbs, sodium, potassium)
    try:
        c.execute(qry)
    except sqlite3.IntegrityError:
        print('ERROR: Food with that name already exists')
    conn.commit()
    conn.close()

def deleteFood(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM food WHERE name="{}"'.format(name))
    conn.commit()
    conn.close()

def deleteMeal(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute( 'DELETE FROM meal \
                WHERE rowid IN ( \
                    SELECT rowid \
                    FROM meal \
                    WHERE DATE(mealDate)=DATE("now") \
                            AND food="{}" \
                    LIMIT 1)'.format(name))
    conn.commit()
    conn.close()
    printDailyStatus()

def addMeal(food):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    foodQryResult = c.execute('SELECT * FROM food WHERE name LIKE "{}%"'.format(food))
    foods = foodQryResult.fetchall()
    if len(foods) > 1:
        print(colorama.Fore.RED+"\n\n\nWHAT??")
        prettyFoods(foods)
    else:
        food = foods[0][0]
        try:
            c.execute('INSERT INTO meal (mealDate, food) VALUES (DATE("now"),"{}")'.format(food))
        except Exception as e:
            print(e)
        conn.commit()
        conn.close()
        printDailyStatus()

def exercise(cal):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO exercise (exerciseDate, cal) VALUES (DATE("now"),"{}")'.format(cal))
    except Exception as e:
        print(e)
    conn.commit()
    conn.close()

def prettyFoods(foods):
    if len(foods)>0:
        for food in foods:
            print(colorama.Fore.YELLOW+"{}::     Cal: {}  Fat: {}g  Protein: {}g  Carbs: {}g  Sodium: {}g  Potassium:  {}g".format(*food))
    else:
        print("\n\n\nYou havent eaten anything dumbass\n\n\n")

def printFoods(startsWith):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM food')
    foods = c.fetchall()
    prettyFoods(foods)

def printDailyStatus():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(  'SELECT food.* \
                FROM food \
                INNER JOIN meal \
                    ON  food.name = meal.food \
                        AND DATE(meal.mealDate)=DATE("now")')
    foods = c.fetchall()
    c.execute('SELECT SUM(exercise.cal) FROM exercise WHERE DATE(exercise.exerciseDate)=DATE("now")')
    ex = c.fetchall()
    pprint(ex)
    calsBurned = ex[0][0]
    print("\n\n\n                   <<<<<EATEN TODAY>>>>>")
    prettyFoods(foods)
    zipped = list(zip(*foods))
    totals = [sum(x) for x in zipped[1:]]
    totals[0]-=int(calsBurned)
    printableTotals = ""
    for nutr in zip(DIET.keys(),totals):
        if nutr[1] > DIET[nutr[0]]:
            printableTotals += colorama.Fore.RED + nutr[0] + ": " + str(nutr[1]) + "g "+ colorama.Fore.RESET
        else:
            printableTotals += colorama.Fore.GREEN + nutr[0] + ": " + str(nutr[1]) + "g "+colorama.Fore.RESET
    print("\n                   <<<<<BURNED " + (colorama.Fore.GREEN if calsBurned > 0 else colorama.Fore.RED) + str(calsBurned) + colorama.Fore.RESET + " CALORIES!>>>>>")
    if len(totals)>0:
        print("                   <<<<<TOTAL>>>>>")
        print(printableTotals)
        zipped = zip(DIET.values(),[-1*x for x in totals])
        remaining = [(0 if sum(x) < 0 else sum(x)) for x in zipped]
        print("                   <<<<<NEED>>>>>")
        print("Cal: {}  Fat: {}g  Protein: {}g  Carbs: {}g  Sodium: {}g  Potassium:  {}g".format(*remaining))


while(1):
    cmd = input('Enter a command, "help", or "quit"\n')
    op = cmd.split()[0]
    if op == "quit":
        break
    if op == "help":
        print("USAGE")
        print(colorama.Fore.RED+"'init'                           - use once to start diet program")
        print("'foods'                          - show all available foods")
        print("'newfood'                        - store a new food option")
        print("'deletefood <food>               - delete food from options")
        print("'eat <food>'                     - track a meal you ate today")
        print("'puke <food>'                    - remove a meal you previously entered today")
        print("'status'                         - print meals eaten and remaining nutritional goals for the day")
        print("'suggest <food1>,<food2>,...'    - suggest foods to eat to meet daily nutritional goals. Optionally add foods you wish to include in the remaining meals")
        print("'nuke diet'                      - delete EVERYTHING")
    if op == "init":
        dietInit()
    if op == "newfood":
        name = input('Name?\n')
        cal = input('# Calories?\n')
        fat = input('g of Fat?\n')
        protein = input('g of Protein?\n')
        carbs = input('g of Carbs?\n')
        sodium = input('g of Sodium?\n')
        potassium = input('g of Potassium?\n')
        print("DONE\n\n")
        addFood(name,cal,fat,protein,carbs,sodium,potassium)
    if op == "eat":
        addMeal(" ".join(cmd.split()[1:]))
    if op == "puke":
        deleteMeal(" ".join(cmd.split()[1:]))
    if op == "burn":
        exercise(int(cmd.split()[1]))
    if op == "status":
        printDailyStatus()
    if op == "foods":
        printFoods('')
    if op == "deletefood":
        deleteFood(" ".join(cmd.split()[1:]))
    if op == "nuke":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('DROP TABLE food')
        c.execute('DROP TABLE meal')
        conn.commit()
        conn.close()



