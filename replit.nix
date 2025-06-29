{ pkgs }: {
  deps = [
    pkgs.unzip
    pkgs.zip
    pkgs.firefox
    pkgs.nodejs_20
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.playwright-driver.browsers
    pkgs.chromium
  ];
  env = {
    PLAYWRIGHT_BROWSERS_PATH = "${pkgs.playwright-driver.browsers}";
    PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = "true";
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1";
  };
}