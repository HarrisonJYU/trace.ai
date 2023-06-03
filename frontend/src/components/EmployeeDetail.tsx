import styled from "styled-components";

const Container = styled.div``;

export const EmployeeDetail = ({ employee }: { employee: User }) => {
    // display employee details
    return (
        <Container>
            <p>{employee.name}</p>
            <p>{employee.email}</p>
            <img src={employee.timeGraph} alt={"time graph"} />
            <img src={employee.clustersGraph} alt={"cluster graph"} />
        </Container>
    );
};
