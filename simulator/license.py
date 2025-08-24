class License:
    def __init__(self, license_name, license_count):
        self.license_name = license_name
        self.license_count = license_count

    def __repr__(self):
        return f"License(name={self.license_name}, count={self.license_count})"