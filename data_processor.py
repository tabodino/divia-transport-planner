from src.etl.load_gtfs import GTFSLoader


def main():
    loader = GTFSLoader()
    loader.run_etl()


if __name__ == '__main__':
    main()
