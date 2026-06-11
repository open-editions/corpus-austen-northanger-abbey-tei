{
  description = "Development environment for Northanger Abbey TEI project";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        pythonWithDeps = python.withPackages (ps: with ps; [
          beautifulsoup4
          pyoxigraph
          httpx
          lxml
          typer # libroj dependency
          rdflib # libroj dependency
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonWithDeps
            pkgs.libxml2
          ];
          shellHook = ''
            export PYTHONPATH="$PYTHONPATH:/home/jon/Programaroj/libroj/src"
          '';
        };
      }
    );
}
