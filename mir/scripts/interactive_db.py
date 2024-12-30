import sqlite3
import time
import readline

if __name__ == "__main__":
    c = sqlite3.connect("data/msmarco-sqlite-index.db", autocommit=False)
    def query(q):
        start_time = time.time()
        results = c.execute(q).fetchall()
        for r in results:
            print(r)
        print(f"{len(results)} results in {time.time() - start_time}s")

    try:
        while True:
            q = input("\033[92mSQL> \033[0m")
            if q == "exit":
                break
            try:
                query(q)
            except sqlite3.Error as e:
                print(f"\033[91m{e}\033[0m")
    except KeyboardInterrupt:
        pass
