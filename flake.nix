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

    poetry2nixFlake = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };


  };

  outputs = inputs@{ self, nixpkgs, flake-utils, pre-commit-hooks, ... }:

    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ inputs.poetry2nixFlake.overlay ];
        };

        lib = pkgs.lib;

        nix-filter = inputs.nix-filter.lib;
        python = pkgs.python3;

        preferWheels = true;

        overrides = pkgs.poetry2nix.overrides.withDefaults (self: super: {
          mypy = super.mypy.overridePythonAttrs (old: { patches = [ ]; });
          pytoolconfig = super.pytoolconfig.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.pdm-pep517 ]; });
          jsonschema = super.jsonschema.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.hatch-fancy-pypi-readme ]; });
          jupyter-core = super.jupyter-core.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.hatchling ]; });
          nbformat = super.nbformat.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.flit ]; });
          seaborn = super.seaborn.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.flit ]; });
          pandas-stubs = super.pandas-stubs.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.poetry ]; });
          contourpy = super.contourpy.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.pybind11 ]; });
          elasticsearch-stubs = super.elasticsearch-stubs.overridePythonAttrs (old: { nativeBuildInputs = old.nativeBuildInputs ++ [ self.setuptools ]; });
          # numpy = super.numpy.override { preferWheel = true; };
          # polars = super.polars.override { preferWheel = true; };
          nbconvert = super.nbconvert.overridePythonAttrs (old: { postPatch = if preferWheels then null else old.postPatch; });
          mrjob = super.mrjob.overridePythonAttrs (old: {
            nativeBuildInputs = old.nativeBuildInputs ++ [ self.setuptools ];
            postInstall = ''
              sed -i 's/ZipFile(path, /& strict_timestamps=False, /' $out/lib/${python.libPrefix}/site-packages/mrjob/util.py
            '';
          });
        });

        lab1-data =
          let
            host = "www.cs.upc.edu/~caim/lab/";
            novels = pkgs.fetchzip {
              url = host + "novels.zip";
              sha256 = "1wz8cjp6320wn7hpdm8x2w578qkka6jagjanlxdql7lr6sl4vwy5";
            };

            arxiv_abs = pkgs.fetchzip {
              url = host + "arxiv_abs.zip";
              stripRoot = false;
              sha256 = "sha256-JoWwuKaI29iO0eQEQhFsmv0ZsgwWWgPia3RqthRg9uU=";
            };

            # For newsgroups we do not use fetchzip since it has too many files
            # for nix to handle the recursive hash
            newsgroups = pkgs.fetchurl {
              url = host + "20_newsgroups.zip";
              sha256 = "sha256-w0xDJZ8d9J+k6DYzh/SEIbIODZphfW5q1xR+rl1QFP8=";
            };
          in
          pkgs.runCommand "lab1-data"
            {
              buildInputs = [ pkgs.unzip ];
            } ''
            mkdir -p $out
            ln -s ${novels} $out/novels
            ln -s ${arxiv_abs} $out/arxiv_abs
            unzip ${newsgroups} -d $out
          '';

        py-env = { groups ? [ ] }: pkgs.poetry2nix.mkPoetryEnv {
          inherit python preferWheels overrides groups;
          pyproject = ./pyproject.toml;
          poetrylock = ./poetry.lock;
          projectDir = "";
        };

        lab-list = with lib; builtins.attrNames (filterAttrs
          (name: type: type == "directory" && hasPrefix "lab" name)
          (builtins.readDir "${./.}"));

      in
      {
        checks = {
          pre-commit-check = pre-commit-hooks.lib.${system}.run {
            src = ./.;
            hooks = {
              black.enable = true;
              isort.enable = true;
              nixpkgs-fmt.enable = true;
              shfmt.enable = true;
              shellcheck = {
                enable = true;
                types_or = lib.mkForce [ ];
              };
            };
          };
        };

        packages =
          let
            SOURCE_DATE_EPOCH = self.lastModified;
            build-figures = name: pkgs.stdenvNoCC.mkDerivation {
              name = "${name}-figures";
              inherit SOURCE_DATE_EPOCH;
              src = nix-filter.filter {
                root = ./${name};
                exclude = [
                  ".gitignore"
                  ".envrc"
                  "assignment.pdf"
                  (nix-filter.matchExt "sh")
                  (nix-filter.matchExt "md")
                  ".latexmkrc"
                  (nix-filter.matchExt "tex")
                  (nix-filter.matchExt "bib")
                ];
              };
              buildInputs =
                let
                  python-env = py-env { groups = [ name ]; };
                in
                [ python-env pkgs.texlive.combined.scheme-full ];
              doCheck = false;
              dontInstall = true;
              buildPhase = ''
                runHook preBuild

                python3 process.py --output $out/figures --format=pdf
                cp -r tables $out || true
                cp -r images $out || true

                runHook postBuild
              '';
            };

            build-report = name: with builtins;
              let
                hasTex = pathExists ./${name}/report.tex;
                hasMd = pathExists ./${name}/report.md;
                hasLatexmk = pathExists ./${name}/.latexmkrc;
              in
              assert lib.assertMsg (hasTex || hasMd) "Missing report.tex or report.md";
              assert lib.assertMsg (hasTex -> !hasMd) "Cannot have both report.tex and report.md";
              assert lib.assertMsg (hasTex -> hasLatexmk) "Missing .latexmkrc";
              (if hasTex then build-report-tex else build-report-md) name;

            build-report-tex = name: pkgs.runCommand "${name}-report"
              {
                inherit SOURCE_DATE_EPOCH;
                src = nix-filter.filter {
                  root = ./${name};
                  include = [
                    ".latexmkrc"
                    (nix-filter.matchExt "tex")
                    (nix-filter.matchExt "bib")
                    (nix-filter.matchExt "lua")
                    "lua"
                  ];
                };
                nativeBuildInputs = with pkgs; [
                  python3.pkgs.pygments
                  which
                  texlive.combined.scheme-full
                  outils
                ];
              }
              ''
                mkdir -p build $out
                export HOME=$(mktemp -d)
                lndir -silent "${build-figures name}" build
                lndir -silent "$src" build
                ln -s "${./common}" common
                cd build
                latexmk
                cp report.pdf $out/$name.pdf
              '';

            build-report-md = name: pkgs.runCommand "${name}-report"
              {
                inherit SOURCE_DATE_EPOCH;
                src = ./${name}/report.md;

                buildInputs = with pkgs; [
                  pandoc
                  texlive.combined.scheme-full
                  outils
                ];
              }
              ''
                mkdir -p build $out
                lndir -silent "${build-figures name}" build
                ln -s "${./common}" common
                cd build
                pandoc -o "$out/$name.pdf" $src
              '';

            zip-derivation = drv: pkgs.runCommand "${drv.name}-zip"
              { buildInputs = with pkgs; [ zip ]; }
              ''
                mkdir -p $out
                cd ${drv}
                zip -r $out/${drv.name}.zip .
              '';

            bundle-deliverable = report: figures: pkgs.runCommand
              (lib.removeSuffix "-report" report.name)
              { buildInputs = with pkgs; [ outils ]; }
              ''
                mkdir -p $out/{extras,src}

                lndir -silent ${report} $out
                lndir -silent ${figures} $out/extras
                lndir -silent ${figures.src} $out/src

                ln -s ${./poetry.lock} $out/src/poetry.lock
                ln -s ${./pyproject.toml} $out/src/pyproject.toml
              '';

            lab-reports = builtins.map build-report lab-list;
            lab-figures = builtins.map build-figures lab-list;
            lab-all = lib.zipListsWith bundle-deliverable lab-reports lab-figures;
            lab-deliverables = builtins.map zip-derivation lab-all;

            derivations = with builtins; listToAttrs (
              map (drv: lib.nameValuePair drv.name drv)
                (concatLists [ lab-reports lab-figures lab-deliverables lab-all ]));
          in
          {
            default = self.packages.${system}.reports;

            reports = pkgs.symlinkJoin {
              name = "reports";
              paths = lab-reports;
            };

            figures = pkgs.linkFarmFromDrvs
              "figures"
              lab-figures;

            deliverables = pkgs.symlinkJoin {
              name = "deliverables";
              paths = lab-deliverables;
            };

            labs = pkgs.linkFarmFromDrvs
              "labs"
              lab-all;

          } // derivations;

        devShells =
          let
            build-shell =
              { name
              , groups ? [ "dev" name ]
              }: pkgs.mkShellNoCC {
                name = "python-poetry-${name}";

                DATA = lab1-data;

                buildInputs =
                  let
                    python-env = py-env { inherit groups; };
                  in
                  with pkgs;[
                    poetry
                    python-env
                    nixpkgs-fmt
                    pandoc
                    texlive.combined.scheme-full
                    parallel
                    bc
                  ];

                inherit (self.checks.${system}.pre-commit-check) shellHook;
              };

            shells = with builtins; listToAttrs (map (name: lib.nameValuePair name (build-shell { inherit name; })) lab-list);

          in
          {
            default = self.devShells.${system}.all;
            all = build-shell { name = "all"; groups = [ "dev" ] ++ lab-list; };
          } // shells;
      });
}
