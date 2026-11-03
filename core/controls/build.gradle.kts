plugins {
    id("tuikio.kotlin-library")
}

dependencies {
    api(project(":core:terminal"))
    api(project(":core:catalog"))
}

// ControlLayoutTest lays out every profile in catalog/profiles: rerun it when they change.
tasks.test { inputs.dir(rootProject.file("catalog/profiles")).withPathSensitivity(PathSensitivity.RELATIVE) }
