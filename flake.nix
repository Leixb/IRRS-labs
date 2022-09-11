{
  description = "Python environment managed with poetry and flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    flake-utils.url = "github:numtide/flake-utils";
    nix-filter.url = "github:numtide/nix-filter";

    nltk_data_src = {
      url = "github:nltk/nltk_data";
      flake = false;
    };

  };
  outputs = inputs@{ nixpkgs, flake-utils, nltk_data_src, ...}:

  flake-utils.lib.eachDefaultSystem (system:
  let
    pkgs = import nixpkgs { inherit system; };

    NLTK_DATA = let
      collection = "all";
    in pkgs.stdenvNoCC.mkDerivation rec {
      pname = "nltk_data";
      version = nltk_data_src.rev;

      src = nltk_data_src;

      dontConfigure = true;
      dontBuild = true;
      dontFixup = true;

      nativeBuildInputs = with pkgs; [ python2 unzip ];

      # Despite the name, download.sh does not download anything from the
      # internet
      installPhase = ''
        export NLTK_DATA_DIR=$out
        bash tools/download.sh "${collection}"
      '';
    };

    python = pkgs.python3;

    overrides = pkgs.poetry2nix.overrides.withDefaults (self: super: {
      mypy = super.mypy.overridePythonAttrs (old: { patches = []; });
      pytoolconfig = super.pytoolconfig.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.pdm-pep517 ]; });
      jsonschema = super.jsonschema.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.hatch-fancy-pypi-readme ]; });
      jupyter-core = super.jupyter-core.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.hatchling ]; });
    });

    nix-filter = inputs.nix-filter.lib;

    py-env = pkgs.poetry2nix.mkPoetryEnv {
      inherit python overrides;

      projectDir = nix-filter.filter {
        root = ./.;
        include = [
          "poetry.lock"
          "pyproject.toml"
        ];
      };

      editablePackageSources = { };
    };

  in
  {
    devShells.default = pkgs.mkShellNoCC {
      name = "python-poetry";

      inherit NLTK_DATA;

      LD_LIBRARY_PATH= pkgs.lib.strings.makeLibraryPath (with pkgs;[
        stdenv.cc.cc.lib
      ]);

      buildInputs = [
        python.pkgs.poetry
        py-env
      ];
    };
  });
}
