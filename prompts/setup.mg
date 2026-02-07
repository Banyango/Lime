<<
Follow the instructions in the selected prompt to create your project.
>>


[[ salt/use-uv/use-uv ]]
[[ salt/use-clean-architecture/use-clean-architecture ]]
[[ salt/use-readme/use-readme sections=["description", "installation", "usage", "contributing", "license", "contact"] ]]


@state completed = false
for i in range(3):
    if !result or result.complete:
        [[ create-test ]]
        [[ run test ]]
        [[ run lint ]]

        @tool state

        @effect run




