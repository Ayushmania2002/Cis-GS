@echo off
REM Sphinx build script for Windows.

pushd %~dp0

set SPHINXBUILD=sphinx-build
set SOURCEDIR=source
set BUILDDIR=_build

if "%1"=="" goto html
if "%1"=="html" goto html
if "%1"=="clean" goto clean
if "%1"=="linkcheck" goto linkcheck

:html
%SPHINXBUILD% -b html %SOURCEDIR% %BUILDDIR%/html
goto end

:clean
rmdir /s /q %BUILDDIR% 2>nul
goto end

:linkcheck
%SPHINXBUILD% -b linkcheck %SOURCEDIR% %BUILDDIR%/linkcheck
goto end

:end
popd
