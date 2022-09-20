{
  description = "Python environment managed with poetry and flakes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    flake-utils.url = "github:numtide/flake-utils";
    nix-filter.url = "github:numtide/nix-filter";
    pre-commit-hooks = {
      url = "github:cachix/pre-commit-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };

    nltk_data_src = {
      url = "github:nltk/nltk_data";
      flake = false;
    };

  };

  outputs = inputs@{ self, nixpkgs, flake-utils, pre-commit-hooks, nltk_data_src, ... }:

    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        NLTK_DATA =
          let
            collection = "all";
          in
          pkgs.stdenvNoCC.mkDerivation rec {
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
          mypy = super.mypy.overridePythonAttrs (old: { patches = [ ]; });
          pytoolconfig = super.pytoolconfig.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.pdm-pep517 ]; });
          jsonschema = super.jsonschema.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.hatch-fancy-pypi-readme ]; });
          jupyter-core = super.jupyter-core.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.hatchling ]; });
          nbformat = super.nbformat.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.flit ]; });
          seaborn = super.seaborn.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.flit ]; });
          pandas-stubs = super.pandas-stubs.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.poetry ]; });
          contourpy = super.contourpy.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.pybind11 ]; });
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
        devShells = {
          default = pkgs.mkShellNoCC {
            name = "python-poetry";

            inherit NLTK_DATA;

            buildInputs = [
              python.pkgs.poetry
              py-env
              pkgs.nixpkgs-fmt
              pkgs.pandoc
              pkgs.texlive.combined.scheme-full
            ];

            inherit (self.checks.${system}.pre-commit-check) shellHook;
          };
        };

        checks = {
          pre-commit-check = pre-commit-hooks.lib.${system}.run {
            src = ./.;
            hooks = {
              black.enable = true;
              isort.enable = true;
              nixpkgs-fmt.enable = true;
            };
          };
        };

        packages =
          let
            build-report = name: pkgs.runCommandWith
              {
                name = "${name}-report";

                derivationArgs = {
                  buildInputs = with pkgs; [
                    pandoc
                    texlive.combined.scheme-full
                  ];
                };

              }
              ''
                mkdir -p $out
                pandoc -o $out/${name}-report.pdf ${./${name}/report.md}
              '';

            lab-reports = with pkgs.lib builtins;
              mapAttrs (name: _: build-report name)
                (filterAttrs
                  (name: type: type == "directory" && hasPrefix "lab" name)
                  (readDir "${./.}"));
          in
          {
            default = pkgs.symlinkJoin {
              name = "reports";
              paths = builtins.attrValues lab-reports;
            };

          } // lab-reports;

      });
}
