{
  description = "Saakshi Backend — Pedestrian accessibility evidence checker";

  inputs = {
    nixpkgs.url = "nixpkgs";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forEachSupportedSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
    in
    {
      devShells = forEachSupportedSystem ({ pkgs }: {
        default = pkgs.mkShell {
          packages = [
            pkgs.python312
            pkgs.python312Packages.pip
            pkgs.python312Packages.virtualenv
            pkgs.glib
            pkgs.libGL
            pkgs.zlib
            pkgs.stdenv.cc.cc.lib
          ];

          shellHook = ''
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib pkgs.zlib pkgs.glib pkgs.libGL ]}:$LD_LIBRARY_PATH"
            if [ ! -d ".venv" ]; then
              python3 -m venv .venv
            fi
            source .venv/bin/activate
            export PYTHONPATH="$PWD:$PYTHONPATH"
          '';
        };
      });
    };
}
