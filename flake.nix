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
              pkgs.parallel
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
            build-figures = name: pkgs.stdenvNoCC.mkDerivation {
              name = "${name}-report-figures";
              src = ./${name};
              buildInputs = [ py-env pkgs.texlive.combined.scheme-full ];
              doCheck = false;
              dontInstall = true;
              buildPhase = ''
                python3 process.py --output $out --format=pdf
              '';
            };

            build-report = name: pkgs.runCommandWith
              {
                name = "${name}-report";

                derivationArgs = {
                  src = ./${name}/report.md;

                  buildInputs = with pkgs; [
                    pandoc
                    texlive.combined.scheme-full
                    bash
                  ];

                  FIGURES = build-figures name;
                };
              }
              ''
                mkdir -p $out
                ln -s $FIGURES figures
                pandoc -o "$out/$name.pdf" $src
              '';

            lab-list = with pkgs.lib; filterAttrs
              (name: type: type == "directory" && hasPrefix "lab" name)
              (builtins.readDir "${./.}");

            map-lab = fn: builtins.mapAttrs (name: _: fn name) lab-list;

            lab-reports = map-lab build-report;
            lab-figures = map-lab build-figures;
          in
          {
            default = self.packages.${system}.all;

            all = pkgs.symlinkJoin {
              name = "reports";
              paths = builtins.attrValues lab-reports;
            };

            all-figures = pkgs.linkFarmFromDrvs
              "reports-figures"
              (builtins.attrValues lab-figures);

          } // lab-reports;

      });
}
