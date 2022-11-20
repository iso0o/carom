# shell.nix
{ pkgs ? import <nixpkgs> {} }:
let
  env-python = pkgs.python3;
  env-python-with-packages = env-python.withPackages (p: with p; [
    pygame
    pymunk
    # other python packages you want
  ]);
in
pkgs.mkShell {
  buildInputs = [
    env-python-with-packages
    # other non python dependencies
  ];
  shellHook = ''
    PYTHONPATH=${env-python-with-packages}/${env-python-with-packages.sitePackages}
    # maybe set more env-vars
  '';
}

